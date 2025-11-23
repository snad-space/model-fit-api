import json
from typing import Literal, List, Dict

import numpy as np
import pandas as pd
import sncosmo
import math
from astropy.table import Table
from fastapi import FastAPI
from pydantic import BaseModel


app = FastAPI()


class Observation(BaseModel):
    mjd: float
    band: str
    flux: float
    fluxerr: float
    zp: float = 8.9
    zpsys: Literal["ab", "vega"] = "ab"


class Target(BaseModel):
    light_curve: List[Observation]
    ebv: float
    name_model: str
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
    brightness_type: str
    band_ref: Dict[str, float]

class Point(BaseModel):
    time: float
    bright: float
    band: str


class Parameters(BaseModel):
    degrees_of_freedom: int
    covariance: List[List[float]]
    chi2: float
    parameters: Dict[str, float]
    
    
class Bright(BaseModel):
    bright: List[Point]


def fit(data, name_model, ebv, redshift):
    dust = sncosmo.CCM89Dust()
    model = sncosmo.Model(source=name_model, effects=[dust], effect_names=["mw"], effect_frames=["obs"])
    model.set(mwebv=ebv)
    fit_params = model.param_names
    fit_params.remove('mwr_v')
    fit_params.remove('mwebv')
    summary, fitted_model = sncosmo.fit_lc(
        data, model, fit_params, bounds={"z": (redshift[0], redshift[1])}
    )
    return summary, fitted_model


def get_bright(data: Model_data):
    dust = sncosmo.CCM89Dust()
    fitted_model = sncosmo.Model(source=data.name_model, effects=[dust], effect_names=["mw"], effect_frames=["obs"])
    fitted_model.set(**data.parameters)
    segment = np.linspace(data.t_min, data.t_max, data.count)
    points = []
    for band in data.band_list:
        predicts = fitted_model.bandflux(band, segment, data.zp, data.zpsys)
        if data.brightness_type == 'flux':
            predicts = [f + data.band_ref[band[0]+band[-1]] for f in predicts]
        elif data.brightness_type == 'diffmag':
            predicts = [math.log(f)/math.log(10)*(-2.5) + 8.9 if f > 0 else None for f in predicts]
        elif data.brightness_type == "mag":
            predicts = [math.log(f + data.band_ref[band[0]+band[-1]])/math.log(10)*(-2.5) + 8.9 if f + data.band_ref[band[0]+band[-1]] > 0 else None for f in predicts]
        points += [Point(time=time, bright=flux, band=band) for time, flux in zip(segment, predicts)]
    return Bright(
        bright=points
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
async def sn_cosmo_fit(data: Target):
    """Fit light curve with sncosmo."""
    return get_params(data)
    

@app.post("/api/v1/sncosmo/get_curve")
async def sn_cosmo_get_curve(data: Model_data):
    """Fit light curve with sncosmo."""
    return get_bright(data)


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
    "v19-1993j",
    "v19-1998bw",
    "v19-1999em",
    "v19-2009ip",
    ]
    return {"models": models}
