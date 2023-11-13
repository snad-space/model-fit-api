import json
from typing import Literal, List, Dict

import numpy as np
import pandas as pd
import sncosmo
from astropy.table import Table
from fastapi import FastAPI
from pydantic import BaseModel

models = ['nugent-sn1a', 'nugent-sn91t', 'nugent-sn91bg', 'nugent-sn1bc', 'nugent-hyper', 'nugent-sn2n',
          'nugent-sn2p', 'nugent-sn2l', 'salt2', 'salt3-nir', 'salt3', 'snf-2011fe', 'v19-1993j',
          'v19-1998bw', 'v19-1999em', 'v19-2009ip']
app = FastAPI()


class Observation(BaseModel):
    mjd: float
    flux: float
    fluxerr: float
    zp: float = 8.9
    zpsys: Literal["ab", "vega"] = "ab"
    band: str


class Target(BaseModel):
    light_curve: List[Observation]
    ebv: float
    t_min: float
    t_max: float
    count: int
    name_model: str
    redshift: List[float]


class Point(BaseModel):
    time: float
    flux: float
    band: str


class Result(BaseModel):
    flux_jansky: List[Point]
    degrees_of_freedom: int
    covariance: List[List[float]]
    chi2: float
    parameters: Dict[str, float]


def fit(data, name_model, ebv, redshift):
    dust = sncosmo.CCM89Dust()
    model = sncosmo.Model(source=name_model, effects=[dust], effect_names=["mw"], effect_frames=["obs"])
    model.set(mwebv=ebv)
    summary, fitted_model = sncosmo.fit_lc(
        data, model, model.param_names, bounds={"z": (redshift[0], redshift[1])}
    )
    return summary, fitted_model


def get_flux_and_params(summary, data, fitted_model, t_min, t_max, count):
    segment = np.linspace(t_min, t_max, count)
    df = data.to_pandas()
    points = []
    for band in df["band"].unique():
        predicts = fitted_model.bandflux(band, segment, df["zp"][0], df["zpsys"][0])
        points += [Point(time=time, flux=flux, band=band) for time, flux in zip(segment, predicts)]
    return Result(
        flux_jansky=points,
        parameters=dict(zip(summary.param_names, summary.parameters)),
        degrees_of_freedom=summary.ndof,
        covariance=summary.covariance.tolist(),
        chi2=summary.chisq,
    )


def approximate(data: Target):
    df = pd.DataFrame([obs.model_dump() for obs in data.light_curve])
    table = Table.from_pandas(df)
    summary, fitted_model = fit(table, data.name_model, data.ebv, data.redshift)
    result = get_flux_and_params(summary, table, fitted_model, data.t_min, data.t_max, data.count)
    return result


@app.post("/api/v1/sncosmo")
async def sn_cosmo(data: Target):
    """Fit light curve with sncosmo."""
    return approximate(data)


@app.get('/api/v1/models')
async def models(data: Target):
    return {'models': models}
