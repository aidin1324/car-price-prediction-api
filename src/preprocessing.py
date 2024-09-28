from sklearn.base import BaseEstimator, TransformerMixin
import pandas as pd
import numpy as np
from sklearn.decomposition import PCA
from sklearn.preprocessing import OneHotEncoder


class PreparingDataService(BaseEstimator, TransformerMixin):
    d_to_fill = None
    mileage_median = None
    mark_map, model_map = None, None
    pca_location_data = None
    one_hot = None

    def fit(self, _X, y=None):
        X = _X.copy()

        X["mileage"] = X["mileage"].str.replace("км", "").str.replace(" ", "").apply(
            lambda x: x if pd.isna(x) else int(x)
        )
        self.d_to_fill = X.groupby(["mark", "model"])["mileage"].median().to_dict()
        self.mileage_median = X["mileage"].median()
        self.mark_map = X["mark"].value_counts()
        self.model_map = X["model"].value_counts()

        self.one_hot = OneHotEncoder(sparse_output=False, handle_unknown="ignore")
        self.one_hot.fit(X[["location"]])
        loc_one_hot = self.one_hot.transform(X[["location"]])

        self.pca_location_data = PCA(n_components=6)
        self.pca_location_data.fit(loc_one_hot)
        return self

    def transform(self, _X, y=None):
        X = _X.copy()
        X["v_engine"] = X["v_engine"].fillna("0")

        X["v_engine"] = X["v_engine"].str.replace("л.", "", regex=False).astype(np.float16)

        X["mileage"] = X["mileage"].str.replace("км", "").str.replace(" ", "").apply(
            lambda x: x if pd.isna(x) else int(x)
        )
        X["mileage"] = X[["mark", "model", "mileage"]].apply(
            lambda x: self.d_to_fill.get(
                (x["mark"], x["model"])
            ) if pd.isna(x["mileage"]) else x["mileage"], axis=1
        )
        # если таких марк * моделей нет
        X["mileage"] = X["mileage"].fillna(self.mileage_median)

        X["year"] = X["year"].str.replace("г.", "", regex=False).astype(np.int16)

        X["sw_location"] = X["sw_location"].map({
            'руль слева\xa0\xa0\xa0новый': 0,
            "руль слева": 0,
            "руль справа": 1
        })

        X["color"] = X["color"].apply(
            lambda x: x if x in [
                'белый',
                'черный',
                'серый',
                'серебристый'
            ] else "others"
        )
        X["body_type"] = X["body_type"].apply(
            lambda x: x if x in [
                'внедорожник5дв.',
                'седан',
                'хэтчбек5дв.'
            ] else "others"
        )
        X["mark"] = X["mark"].map(self.mark_map)

        X["model"] = X["model"].map(self.model_map)

        X["mark"] = X["mark"].fillna(1)  # не встречался ранее
        X["model"] = X["model"].fillna(1)

        loc_one_h = self.one_hot.transform(X[["location"]])
        X = X.drop("location", axis=1)
        X[
            ["PCA0",
             "PCA1",
             "PCA2",
             "PCA3",
             "PCA4",
             "PCA5"
             ]
        ] = self.pca_location_data.transform(loc_one_h)
        X["sw_location"] = X["sw_location"].fillna(0)  # руль слева
        X = pd.get_dummies(X, columns=["gearbox", "color", "fuel_type", "body_type"])
        return X
