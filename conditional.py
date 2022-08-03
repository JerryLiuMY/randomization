import numpy as np
from scipy.stats import truncnorm
from functools import partial

X = [0.813267813267813, 0.612068965517241, 0.713670613562971, 0.922330097087379, 0.81270182992465,
     0.980603448275862, 0.891891891891892, 0.780409041980624, 1.51619870410367, 0.786637931034482,
     0.92572658772874, 1.27076591154261, 1.02909482758621, 1.4217907227616, 0.81270182992465,
     1.50699677072121, 0.575135135135135, 1.33620689655172, 1.02047413793103, 0.528586839266451,
     0.862068965517241, 1.11530172413793, 1.10118406889128, 1.22306034482759, 0.808189655172414,
     1.24379719525351, 0.905172413793104, 1.40280777537797, 0.811218985976268, 0.88133764832794,
     0.69073275862069, 1.26049515608181, 0.579288025889968, 0.702586206896552, 0.890301724960064,
     0.964439655172413, 0.92170626349892]

SIGMA = np.diag(
    [0.00400616351128161, 0.030059017384886, 0.102029725567161, 0.088658020114521, 0.104295636149854,
     0.0737445782342327, 0.0654365980297311, 0.0518042635802516, 0.12079318490481, 0.0684821760626574,
     0.0644857835659649, 0.255533140108395, 0.102640335212518, 0.153208002787522, 0.0592803935368147,
     0.211508149115732, 0.0401274251080888, 0.184853763479433, 0.0659587393534699, 0.0212852032792557,
     0.0517431174146126, 0.0817138529228554, 0.0995694163979758, 0.0917188736769625, 0.071057820115819,
     0.12137947379161, 0.0620537018481698, 0.130066325704489, 0.0460172568626761, 0.0563916115263375,
     0.0371677136381132, 0.0955191702042282, 0.0330349869841438, 0.0397080226677499, 0.090992021208343,
     0.0892513406062135, 0.0530575476212782]
)

NDRAWS = 10000
ALPHA = 0.05
BETA = 0.005

# DRAW FROM THE STANDARD NORMAL DISTRIBUTION WITH FIXED SEED.
# REPLICATE THE VECTOR OF ESTIMATES.
# REPLICATE THE VARIANCE MATRIX.
INPUT = np.random.normal(size=len(X) * NDRAWS).reshape(NDRAWS, -1)
Y = X
SIGMA = np.kron(np.array([[1, 1], [1, 1]]), SIGMA)


# APPROXIMATION OF THE CUMULATIVE DISTRIBUTION FUNCTION (I.E., X[I] <= Q) OF THE
# TRUNCATED NORMAL DISTRIBUTION, WHERE WHERE (A,B) ARE THE TRUNCATION POINTS AND
# THE MEAN IS MU.
def PTRN2(MU, Q, A, B, SIGMA, N, SEED=100):
    np.random.seed(SEED)
    TAIL_PROB = np.mean(
        truncnorm.ppf(q=np.random.uniform(N), a=[(A - MU) / SIGMA] * N, b=np.array([(B - MU) / SIGMA] * N) + MU) <=
        ((Q - MU) / SIGMA)
    )

    return TAIL_PROB


# The number of treatment arms and the index of the winning arm
K = len(X)
theta_tilde = np.argmax(X)

# The estimate associated with the winning arm
YTILDE = Y[theta_tilde]

# i) variance of all the estimates
# ii) variance fo the winning arm
# iii) covariance of the winning arm and other arms
SIGMAYTILDE = SIGMA[K + theta_tilde, K + theta_tilde]
SIGMAXYTILDE_VEC = np.array(SIGMA[(K + theta_tilde), 0:K])
SIGMAXYTILDE = SIGMA[theta_tilde, (K + theta_tilde)]

# normalised difference between each treatment arm and winning arm
ZTILDE = np.array(X) - (SIGMA[(K + theta_tilde), 0:K]) / SIGMAYTILDE * YTILDE

# the lower truncation value
IND_L = SIGMAXYTILDE_VEC < SIGMAXYTILDE
if sum(IND_L) == 0:
    LTILDE = -np.inf
if sum(IND_L) > 0:
    LTILDE = max(SIGMAYTILDE * (ZTILDE[IND_L] - ZTILDE[theta_tilde]) / (SIGMAXYTILDE - SIGMAXYTILDE_VEC[IND_L]))

# the upper truncation value
IND_U = SIGMAXYTILDE_VEC > SIGMAXYTILDE
if sum(IND_U) == 0:
    UTILDE = +np.inf
if sum(IND_U) > 0:
    UTILDE = min(SIGMAYTILDE * (ZTILDE[IND_U] - ZTILDE[theta_tilde]) /
                 (SIGMAXYTILDE - SIGMAXYTILDE_VEC[IND_U]))

# the V truncation value
IND_V = (SIGMAXYTILDE_VEC == SIGMAXYTILDE)
if sum(IND_V) == 0:
    VTILDE = 0
if sum(IND_V) > 0:
    VTILDE = min(-(ZTILDE[IND_V] - ZTILDE[theta_tilde]))

""" MED_U_ESTIMATE (MEDIAN UNBIASED ESTIMATE) """
YHAT = YTILDE
SIGMAYHAT = SIGMAYTILDE
L = LTILDE
U = UTILDE
SIZE = 0.5
NMC = NDRAWS

CHECK_UNIROOT = False
k = K

while CHECK_UNIROOT is False:
    SCALE = k
    MUGRIDSL = YHAT - SCALE * np.sqrt(SIGMAYHAT)
    MUGRIDSU = YHAT + SCALE * np.sqrt(SIGMAYHAT)
    MUGRIDS = [np.float(MUGRIDSL), np.float(MUGRIDSU)]
    PTRN2_ = partial(PTRN2, Q=YHAT, A=L, B=U, SIGMA=np.sqrt(SIGMAYHAT), N=NMC)
    INTERMEDIATE = np.array(list(map(PTRN2_, MUGRIDS))) - (1 - SIZE)
    HALT_CONDITION = abs(max(np.sign(INTERMEDIATE)) - min(np.sign(INTERMEDIATE))) > tol
    if HALT_CONDITION is True:
        CHECK_UNIROOT = True
    if HALT_CONDITION is False:
        k = 2 * k

# INITIALISE LOOP.
HALT_CONDITION = False
MUGRIDS = [0] * 3

# SIMPLE BISECTION SEARCH ALGORITHM.
while HALT_CONDITION is False:
    MUGRIDSM = (MUGRIDSL + MUGRIDSU) / 2
    PREVIOUS_LINE = MUGRIDS
    MUGRIDS = [np.float(MUGRIDSL), np.float(MUGRIDSM), np.float(MUGRIDSU)]
    PTRN2_ = partial(PTRN2, Q=YHAT, A=L, B=U, SIGMA=np.sqrt(SIGMAYHAT), N=NMC)
    INTERMEDIATE = np.array(list(map(PTRN2_, MUGRIDS))) - (1 - SIZE)

    if max(abs(MUGRIDS - PREVIOUS_LINE)) == 0:
        HALT_CONDITION = True

    if (abs(INTERMEDIATE[1]) < tol) or (abs(MUGRIDSU - MUGRIDSL) < tol):
        HALT_CONDITION = True

    if np.sign(INTERMEDIATE[0]) == np.sign(INTERMEDIATE[1]):
        MUGRIDSL = MUGRIDSM

    if np.sign(INTERMEDIATE[2]) == np.sign(INTERMEDIATE[1]):
        MUGRIDSU = MUGRIDSM

    PYHAT = MUGRIDSM

MED_U_ESTIMATE = PYHAT


# COMPUTATION OF THE MEAN OF THE TRUNCATED NORMAL DISTRIBUTION, WHERE (A,B) ARE
# THE TRUNCATION POINTS AND THE MEAN IS MU.
def ETRN2(MU, A, B, SIGMA, N, SEED=100):
    np.random.seed(SEED)
    TAIL_PROB = SIGMA * np.mean(
        truncnorm.ppf(q=np.random.uniform(N), a=[(A - MU) / SIGMA] * N, b=np.array([(B - MU) / SIGMA] * N) + MU)
    )

    return TAIL_PROB


# FINDS THE THRESHOLD FOR CONFIDENCE REGION EVALUATION.
def CUTRN(MU, Q, A, B, SIGMA, SEED=100):
    np.random.seed(SEED)
    CUT = SIGMA * truncnorm.ppf(q=Q, a=(A - MU) / SIGMA, b=(B - MU) / SIGMA) + MU

    return CUT


# FINDS THE THRESHOLD FOR CONFIDENCE REGION EVALUATION IN THE HYBRID SETTING.
def CHYRN(MU, Q, A, B, SIGMA, CV_BETA, SEED=100):
    np.random.seed(SEED)
    CUT = SIGMA * truncnorm.ppf(p=Q, a=max((A - MU) / SIGMA, -CV_BETA), b=min((B - MU) / SIGMA, +CV_BETA)) + MU

    return CUT
