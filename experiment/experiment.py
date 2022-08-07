from data_prep.data_prep import data_prep
from models.winners import Winners
from models.naive import Naive
from datetime import datetime
import seaborn as sns
import numpy as np
sns.set()


def experiment(model_name, ntreat, diff, nsample):
    """ RUn experiment
    :param model_name: Model name
    :param ntreat: number of treatment
    :param diff: difference between winning arm and the remaining arms
    :param nsample: Number of samples
    :return: coverage rate
    """

    # generate data
    tol = 1e-5
    Y_all, sigma = data_prep(ntreat, diff, nsample)
    model_dict = {"Naive": Naive, "Winners": Winners}
    Model = model_dict[model_name]

    # find coverage rate
    coverage = []
    for idx, Y in enumerate(Y_all):
        # logging massage
        if idx % 100 == 0:
            print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} Working on sample {idx}")

        # logging massage
        model = Model(Y, sigma)
        mu_lower = model.search_mu(alpha=0.025, tol=tol)
        mu_upper = model.search_mu(alpha=1-0.025, tol=tol)

        # append coverage rate
        coverage.append((diff > mu_upper) & (diff < mu_lower))

    return np.mean(coverage)