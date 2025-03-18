import json
from typing import Literal, List, Dict, Optional

import numpy as np
import pandas as pd
import sncosmo
from astropy.table import Table
from fastapi import FastAPI
from pydantic import BaseModel


app = FastAPI()


class Observation(BaseModel):
    mjd: Optional[float]
    band: Optional[str]
    flux: Optional[float]
    fluxerr: Optional[float]
    zp: Optional[float] = 8.9
    zpsys: Literal["ab", "vega"] = "ab"


class Target(BaseModel):
    light_curve: List[Observation]
    ebv: Optional[float]
    t_min: Optional[float]
    t_max: Optional[float]
    count: Optional[int]
    name_model: Optional[str]
    redshift: List[float]


class Model_data(BaseModel):
    parameters: Dict[str, float] 
    name_model: str 
    zp: float 
    zpsys: str 
    band_list: List[str] 
    t_min: float 
    t_max: float 
    count: int

class Point(BaseModel):
    time: Optional[float]
    diffflux_Jy: Optional[float]
    band: Optional[str]


class Parameters(BaseModel):
    degrees_of_freedom: int
    covariance: List[List[float]]
    chi2: float
    parameters: Dict[str, float]
    
    
class Flux(BaseModel):
    flux_jansky: List[Point]


def fit(data, name_model, ebv, redshift):
    dust = sncosmo.CCM89Dust()
    model = sncosmo.Model(source=name_model, effects=[dust], effect_names=["mw"], effect_frames=["obs"])
    model.set(mwebv=ebv)
    summary, fitted_model = sncosmo.fit_lc(
        data, model, model.param_names, bounds={"z": (redshift[0], redshift[1])}
    )
    return summary, fitted_model


def get_flux(data: Model_data):
    dust = sncosmo.CCM89Dust()
    fitted_model = sncosmo.Model(source=data.name_model, effects=[dust], effect_names=["mw"], effect_frames=["obs"])
    fitted_model.set(**data.parameters)
    segment = np.linspace(data.t_min, data.t_max, data.count)
    points = []
    for band in data.band_list:
        predicts = fitted_model.bandflux(band, segment, data.zp, data.zpsys)
        points += [Point(time=time, diffflux_Jy=flux, band=band) for time, flux in zip(segment, predicts)]
    return Flux(
        flux_jansky=points
    )
    
    
def get_params(data: Target):
    df = pd.DataFrame([dict(obs) for obs in data.light_curve])
    table = Table.from_pandas(df)
    summary, fitted_model = fit(table, data.name_model, data.ebv, data.redshift)
    try: cov=summary.covariance.tolist() 
    except: 
        cov=[[]] 
        print('covariance is none')
    return Parameters(
        parameters=dict(zip(summary.param_names, summary.parameters)),
        degrees_of_freedom=summary.ndof,
        covariance=cov,
        chi2=summary.chisq,
    )


@app.post("/api/v1/sncosmo/fit")
async def sn_cosmo(data: Target):
    """Fit light curve with sncosmo."""
    return get_params(data)
    

@app.post("/api/v1/sncosmo/get_bright")
async def sn_cosmo(data: Model_data):
    """Fit light curve with sncosmo."""
    return get_flux(data)


@app.get("/api/v1/models")
async def models():
    models = [
    "nugent-sn1a",
    "nugent-sn91t",
    "nugent-sn91bg",
    "nugent-sn1bc",
    "nugent-hyper",
    "nugent-sn2n",
    "nugent-sn2p",
    "nugent-sn2l",
    "salt2",
    "salt3-nir",
    "salt3",
    "snf-2011fe",
    "v19-1993j",
    "v19-1998bw",
    "v19-1999em",
    "v19-2009ip",
    ]
    return {"models": models}
