import sys
import time
import math
import numpy as np
import matplotlib.pyplot as plt
from scipy.linalg import expm
from ortools.linear_solver import pywraplp

# Print iterations progress
def printProgressBar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█', printEnd = "\r"):
	"""
	Call in a loop to create terminal progress bar
	@params:
	iteration   - Required  : current iteration (Int)
	total       - Required  : total iterations (Int)
	prefix      - Optional  : prefix string (Str)
	suffix      - Optional  : suffix string (Str)
	decimals    - Optional  : positive number of decimals in percent complete (Int)
	length      - Optional  : character length of bar (Int)
	fill        - Optional  : bar fill character (Str)
	printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
	"""
	percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
	filledLength = int(length * iteration // total)
	bar = fill * filledLength + '-' * (length - filledLength)
	print('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix), end = printEnd)
	# Print New Line on Complete
	if iteration == total: 
		print()

# Generate the initial state of the buffer (in which phase is the arrival process when the buffer is empty?)
def initState(D0, D1, B, T):
	phases = len(D0)
	events = [-1] * phases
	g = [-1] * phases
	pInit = [0] * (phases * B)
	if phases > 1:
		l = []
		w = []
		for i in range(phases):
			l.append(D1[i][i])		
			w.append(-(D0[i][i] + D1[i][i]))

		for i in range(phases):
			events[i] = float(l[i])/float(w[i])
			g[i] = events[i]/min(B, math.floor(float(l[i]) * float(T) + 1))

		gTot = np.sum(g)
		for i in range(phases):
			pInit[i] = g[i]/gTot
	else:
		pInit[0] = 1.0

	return pInit

# Generate the Infinitesimal Generator Q of a MAP, given D0 and D1
def generateQ(D0, D1, B):
	if len(D0) != len(D1) or len(D0[0]) != len(D1[0]):
		print ("ERROR: This is not a valid MAP.")
		exit(-1)

	phases = len(D0)
	Z = np.zeros((phases, phases))

	tmp = []
	for i in range(B):
		l = []
		for j in range(B):
			if i==B-1 and j==i:
				l.append(Z)
			elif j==i:
				l.append(D0)
			elif j==i+1:
				l.append(D1)
			else:
				l.append(Z)
		tmp.append(np.hstack(tuple(l)))

	Q = np.vstack(tuple(tmp))

	return Q

# Create an array with the service time of each batch (depending on its size)
def batchServiceTime(B, m, model):
	
	if model == 'InceptionV4':
		t0 = 4.98785373866948
		t1 = 2.21290624531453
		t2 = -0.006302148424865
		t3 = 0.01220707314674
		t4 = -0.001078252966917
		t5 = 0.00000293842054489054
		t6 = -0.000136439880153
		t7 = -0.00000238944435771044
		t8 = 0.00000016826351295629
		t9 = -0.000000000444821512957105
	elif model == 'Resnet':
		t0 = 4.10287326093357
		t1 = 2.44209348386686
		t2 = -0.003744827715921
		t3 = 0.00146578966951
		t4 = -0.001200716327886
		t5 = 0.00000154147156981117
		t6 = 0.000169790388555
		t7 = -0.00000169402238148543
		t8 = 0.000000193096097179588
		t9 = -0.000000000214320561298109
	elif model == 'mxnet-resnet50':
#		t0 = 7.710663849102216
#		t1 = 1.754708102954743
#		t2 = -0.014949769836024564
#		t3 = 0.008564275993968579
#		t4 = -0.0012234754489061973
#		t5 = 0.0000087260407619855
#		t6 = -0.000309124469092023
#		t7 = 0.0000013306423926617268
#		t8 = 0.00000025436598276133704
#		t9 = -0.0000000015428995858712824
		t0 = 4.159625107884683
		t1 = 2.6042179469237112
		t2 = -0.010825805019675406
		t3 = 0.009138187816342925
		t4 = -0.0028596859100282783
		t5 = 0.00000969154925319072
		t6 = -0.0010892145857441117
		t7 = 0.0000017781522992577246
		t8 = 0.000001226979037160046
		t9 = -0.000000003604767989748986
		t10 = 0.000052168371220458194
		t11 = -0.00000030873547472152034
		t12 = 0.000000001335682942382537
		t13 = -0.00000000017570492803764548
		t14 = 0.0000000000004756195437494171
	elif model == 'manual':
		m = 0.036944444444445
		q = 0.007111111111111
#		m = 0.081386111111111
#		q = 0.037277777777778
#		m = 0.230397222222222
#		q = -0.003794444444445
#		m = 0.192
#		q = -0.00095
#		m = 0.193338888888889
#		q = 0.007322222222223
		v = [0] * B

		for i in range(B):
			v[i] = m * (i+1) + q

		return v
	else:
		print('The required model is not supported.')
		exit(-1)

	services = []
	for k in range(1,B+1):
		if model == 'mxnet-resnet50':
			serv = t0 + t1*k + t2*m + t3*k**2 + t4*k*m + t5*m**2 + t6*k**3 + t7*m*k**2 + t8*k*m**2 + t9*m**3 + t10*k**4 + t11*m*k**3 + t12*(k**2)*(m**2) + t13*k*m**3 + t14*m**4
		else:
			serv = t0 + t1*k + t2*m + t3*k**2 + t4*k*m + t5*m**2 + t6*k**3 + t7*m*k**2 + t8*k*m**2 + t9*m**3
		services.append(serv)

	return services

# Get the batch size distribution
def batchProbState(D0, D1, B, T):
	phases = len(D0)
	pInit = initState(D0, D1, B, T)
	Q = generateQ(D0, D1, B)

	p = [0] * B
	pTmp = np.dot(pInit, expm(Q * T))
	i = 0
	j = 0
	while j < phases * B:
		if i < B - 1:
#			p[i] = pTmp[j] + pTmp[j+1]
			p[i] = sum(pTmp[j:j+phases])
		else:
			p[i] = 1 - sum(p)
		i += 1
		j += phases

	return p

# Get the request size distribution
def reqProbState(D0, D1, B, T):
	p = batchProbState(D0, D1, B, T)
	qTmp = [-1] * B
	q = [-1] * B
	for i in range(B):
		qTmp[i] = (i+1) * p[i]
	sum_qTmp = np.sum(qTmp)
	for i in range(B):
		q[i] = qTmp[i]/sum_qTmp

	return q

def getPercentileBatchSize(batchSizeProbState, quantile):
	B = len(batchSizeProbState)
	p = 0.0
	for i in range(0,B):
		if p < quantile and p + batchSizeProbState[i] > quantile:
			return i + 1
		else:
			p += batchSizeProbState[i]

def getPercentileReqSize(reqSizeProb, quantile):
	B = len(reqSizeProb)
	q = 0.0
	for i in range(0,B):
		if q < quantile and q + reqSizeProb[i] > quantile:
			return i + 1
		else:
			q += reqSizeProb[i]

# Determine with which service time the request was served
def findPositionX(B, M, model, x):
	v = batchServiceTime(B, M, model)

	if x < min(v):
		return 0
	elif x > max(v):
		return B-1

	for i in range(B):
#		print("x = " + str(x) + " | i = " + str(i) + " | vm = " + str(v[i]) + " | vM = " + str(v[i+1]))
		if x >= v[i] and x < v[i+1]:
			return i

# Get the CDF of the request latency when the batch service time follows a deterministic distribution
def latencyCdfDetService(D0, D1, B, T, M, model, x):
	phases = len(D0)
	if phases == 2:
		l = []
		w = []
		for i in range(phases):
			l.append(D1[i][i])		
			w.append(-(D0[i][i] + D1[i][i]))

		tau = (B-1) * np.sum(w) / (l[0] * w[1] + l[1] * w[0])
	elif phases == 1:
		l = D1[0]
		tau = (B-1)/l
	else:
		#TODO: derive correctly the value of tau. Now it is T for simplicity, but errors are expected.
		tau = T
		

	q = reqProbState(D0, D1, B, T)
	v = batchServiceTime(B, M, model)
	idx = findPositionX(B, M, model, x)

	if (B == 1 and x < max(v)) or (B > 1 and x < min(v)):
		return 0.0
	elif x > max(v) + min(tau, T):
		return 1.0
	elif x <= v[idx] + T and idx < B-1:
		return ((x - v[idx])/T) * q[idx] + sum(q[0:idx])
	elif x <= v[idx] + T and idx == B-1:
		return ((x - v[idx])/min(tau, T)) * q[idx] + sum(q[0:idx])
	else:
		return sum(q[0:idx+1])

def latencyPercentileDetService(D0, D1, B, T, M, model, x, quantile, err):
	xLow = 0.0
	xUp = x
	xTest = (xUp + xLow) / 2
	perc = latencyCdfDetService(D0, D1, B, T, M, model, xTest)

	while xUp - xLow > err:
		if perc < quantile:
			xLow = xTest
		else:
			xUp = xTest
		xTest = (xUp + xLow) / 2
		perc = latencyCdfDetService(D0, D1, B, T, M, model, xTest)

	return xTest

def averageLatencyExpService(D0, D1, B, T, M, model):
	phases = len(D0)
	if phases == 2:
		l = []
		w = []
		for i in range(phases):
			l.append(D1[i][i])		
			w.append(-(D0[i][i] + D1[i][i]))

		tau = (B-1) * np.sum(w) / (l[0] * w[1] + l[1] * w[0])
	elif phases == 1:
		l = D1[0]
		tau = (B-1)/l
	else:
		#TODO: derive correctly the value of tau. Now it is T for simplicity, but errors are expected.
		tau = T
	
	q = reqProbState(D0, D1, B, T)
	v = batchServiceTime(B, M, model)
	avgLat = 0.0
	for i in range(len(q)):
		avgLat += q[i] * v[i]

	return avgLat

def latencyPercentileExpService(D0, D1, B, T, M, model, x, quantile):
	avgLat = averageLatencyExpService(D0, D1, B, T, M, model)
	perc = -avgLat * np.log(1-quantile)

	return perc

def testModelGraph(xAxisModel, yAxisModel, xAxisTest, yAxisTest):
	plt.figure(figsize=(10,10))
	plt.plot(xAxisModel, yAxisModel, linewidth=3, label='Model')
	plt.plot(xAxisTest, yAxisTest, linewidth=3, label='Data')
	plt.xlabel("t [s]", fontsize=24)
	plt.ylabel("P(R $\leq$ t)", fontsize=24)
	plt.tick_params(axis='both', which='major', labelsize=24)
	plt.legend(loc='lower right', fontsize=24)

	plt.minorticks_on()
	plt.grid(which='major')
	plt.grid(which='minor')

	plt.show()


########## PRINT DATA USED FOR PLOT ##########
def printData(xAxisModel, yAxisModel, xAxisTest, yAxisTest):
	i = 0
	with open('model.dat', 'w') as f:
		while i < len(xAxisModel):
			f.write(str(xAxisModel[i])+'\t'+str(yAxisModel[i])+'\n')
			i += 1

	i = 0
	with open('experiment.dat', 'w') as f:
		while i < len(xAxisTest):
			f.write(str(xAxisTest[i])+'\t'+str(yAxisTest[i])+'\n')
			i += 1

def printError(D0, D1, B, T, xTest):
	qErr = []
	yAxis = np.arange(0,1,0.01)
	for i in yAxis:
		qTest = np.quantile(xTest, i)
		qModel = latencyPercentileDetService(D0, D1, B, T, M, model, 60.0, i, 0.001)
		qMAPE = abs(qTest - qModel) * 100 / qTest
		qErr.append(qMAPE)

	########## Box plot ##########
	print('MAPE = '+str(np.mean(qErr)))
	print('Max APE = '+str(max(qErr)))
	plt.figure(figsize=(10,10))
	plt.boxplot(qErr, 0, '')
	plt.ylabel("Error [%]", fontsize=24)
	plt.tick_params(axis='both', which='major', labelsize=24)
	plt.xticks([])

	########## CDF ##########
#	qErr.sort()
#	plt.figure(figsize=(10,10))
#	plt.plot(qErr, yAxis, linewidth=3)
#	plt.xlabel("x [%]", fontsize=24)
#	plt.ylabel("P(Error $\leq$ x)", fontsize=24)
#	plt.tick_params(axis='both', which='major', labelsize=24)

#	plt.minorticks_on()
#	plt.grid(which='major')
#	plt.grid(which='minor')

	plt.show()

def solveOptimizationProblem(D0, D1, model, quantile, slo, constraint):

	if constraint != 'latency' and constraint != 'cost':
		print('You can optimize either __latency__ or __cost__.')
		exit(-1)

	B=20
	maxTime = 30.0
	err = 0.01
	
	memories = [x for x in range(1280,3008+1,64)]
	timeouts = [x for x in np.arange(0.0001,0.0002,0.0001)]
	matLatency = np.zeros((len(memories), len(timeouts)))
	matCost = np.zeros((len(memories), len(timeouts)))

	count = 0
	total = len(memories * len(timeouts))

	start = time.time()

	i = 0
	while i < len(memories):
		j = 0
		while j < len(timeouts):
			lat = latencyPercentileDetService(D0, D1, B, timeouts[j], float(memories[i]), model, maxTime, quantile, err)
			batchSizeProb = batchProbState(D0, D1, B, timeouts[j])
			batch_size = getPercentileBatchSize(batchSizeProb, quantile)
			matLatency[i][j] = lat
			#print(batchServiceTime(batch_size, memories[i], model)[batch_size-1])
			matCost[i][j] = getCostRequest(batch_size, batchServiceTime(batch_size, memories[i], model)[batch_size-1], memories[i])
			j += 1
			count += 1
			printProgressBar(count, total, prefix = 'Processing:', suffix = 'Complete', length = 50)
		i += 1

########## DEBUG: PRINT DATA ##########
#	print(matLatency)
#	print(matCost)
#	exit(-1)
########## DEBUG: PRINT DATA ##########


	if constraint == 'latency':
		solution = minimizeCost(memories, timeouts, matLatency, matCost, slo)
	else:
		solution = minimizeLatency(memories, timeouts, matLatency, matCost, slo)

	end = time.time()
	print('Time to solve the problem: '+str(end - start)+' seconds.')

	return solution

def minimizeCost(memories, timeouts, matLatency, matCost, slo):
	minCost = -1.0
	countOkay = 0
	countOptimal = 0
	countTotal = 0
	minCostList = []

	i = 0
	while i < len(memories):
		j = 0
		while j < len(timeouts):
			latency = matLatency[i][j]
			cost = matCost[i][j]
			countTotal += 1
			if latency < slo:
				countOkay += 1
				if cost < minCost or minCost == -1.0:
					minCostList.append(cost)
					minCost = cost
					optMem = memories[i]
					optTimeout = timeouts[j]
					trgLat = latency
				elif cost == minCost:					
					minCostList.append(cost)
			j += 1
		i += 1

	if minCost == -1.0:
		print('The problem cannot be solved.')
		exit(-1)
	else:
		for c in minCostList:
			if c == minCost:
				countOptimal += 1

	return (optMem, optTimeout, trgLat, minCost, countOkay, countOptimal, countTotal)

def minimizeLatency(memories, timeouts, matLatency, matCost, slo):
	minLat = -1.0
	countOkay = 0
	countOptimal = 0
	countTotal = 0
	minLatList = []

	i = 0
	while i < len(memories):
		j = 0
		while j < len(timeouts):
			latency = matLatency[i][j]
			cost = matCost[i][j]
			countTotal += 1
			if cost < slo :
				countOkay += 1
				if latency < minLat or minLat == -1.0:
					minLatList.append(latency)
					minLat = latency
					optMem = memories[i]
					optTimeout = timeouts[j]
					trgCost = cost
				elif latency == minLat:
					minLatList.append(latency)
			j += 1
		i += 1

	if minLat == -1.0:
		print('The problem cannot be solved.')
		exit(-1)
	else:
		for l in minLatList:
			if l == minLat:
				countOptimal += 1

	return (optMem, optTimeout, minLat, trgCost, countOkay, countOptimal, countTotal)
	

def getCostRequest(numReqsInBatch, latency, mem):
	numBatch = 1
	freeMem = 0
	freeInvocation = 0
	respBatch = latency
	memGB = mem/1024

	costMemory = (numBatch * respBatch * memGB - freeMem) * 0.0000166667
	costInvocation = (numBatch - freeInvocation) * 0.0000002

	costMemoryRequest = costMemory/numReqsInBatch
	costInvocationRequest = costInvocation/numReqsInBatch

	return costMemoryRequest + costInvocationRequest


DEBUG = True
MODE = 'fitting' #'fitting' or 'solver'
W = 1
B = 1
T = 10.0
M = 1024
model = 'Resnet'

if MODE == 'fitting':
	fname = '/home/riccardo/Desktop/Università_Varie/serverless/AWS_experiments/final/newExp/REAL/20181009_09-10_T37ms_M3008_mobinet/ReqRespTime.dat'
	#fname = '/home/riccardo/Desktop/Università_Varie/serverless/AWS_experiments/results/W14_B20_T10ms_mem3008/ReqRespTime.dat'
	#fname = 'results/W'+str(W)+'/W'+str(W)+'_bs'+str(B)+'_to'+str(T)+'.dat' #File with simulated or measured request latencies
	########### START --- Read matrix from text file ##########
	fnameD0 = '20181011_MAPs/MAP'+str(W)+'_D0'
	fnameD1 = '20181011_MAPs/MAP'+str(W)+'_D1'
	#fnameD0 = 'synthetic_workload/W'+str(W)+'_D0'
	#fnameD1 = 'synthetic_workload/W'+str(W)+'_D1'
	D0 = np.loadtxt(fnameD0, dtype='f', delimiter=',')
	D1 = np.loadtxt(fnameD1, dtype='f', delimiter=',')
	########### END --- Read matrix from text file ##########

	out = []
	memOut = []
	for M in range(1024,3009,64):
		memOut.append(M)
		out.append(latencyPercentileDetService(D0, D1, B, T, M, model, 30, 0.95, 0.01))
	for i in range(len(out)):
		print(str(memOut[i])+'MB -> '+str(out[i]*1000))
	exit(0)

	xModel = np.arange(0,30,0.01)
	yModel = []

	if DEBUG:
		#xModelMax = round(max(xModel))/10
		xModelLen = len(xModel)
		start = time.time()

	for x in xModel:
		yModel.append(latencyCdfDetService(D0, D1, B, T, M, model, x))
		if DEBUG:# and x%xModelMax == 0:
			 printProgressBar(len(yModel), xModelLen, prefix = 'Modeling:', suffix = 'Complete', length = 50)

	if DEBUG:
		print('The model has been generated')
		end = time.time()
		print('Time to generate the model: '+str(end - start)+' seconds.')

	if DEBUG:
		print('Importing data from '+fname+' ...')

	xTest = np.loadtxt(fname)/1000
	xTest.sort()
	lenTest = len(xTest)
	yTest = [float(x)/float(lenTest) for x in range(lenTest)]

	if DEBUG:
		print('Data has been imported.')

	#print(latencyPercentileDetService(D0, D1, B, T, M, model, 15.0, 0.95, 0.001))
	#print(np.quantile(xTest, 0.95))

	testModelGraph(xModel, yModel, xTest, yTest)
#	printData(xModel, yModel, xTest, yTest)
#	printError(D0, D1, B, T, xTest)

	########## Test ##########
	#print(batchServiceTime(1, 1920, 'Resnet'))
	#print(findPositionX(20, 1920, 'Resnet', 3.019809) + 1)
	#print(getCostRequest(2, batchServiceTime(2, 2752, 'Resnet')[1], 2752))
	########## Test ##########
elif MODE == 'solver':
	for i in range(10,11):
		fnameD0 = '20181011_MAPs/MAP'+str(i)+'_D0'
		fnameD1 = '20181011_MAPs/MAP'+str(i)+'_D1'
	#	fnameD0 = 'synthetic_workload/W'+str(W)+'_D0'
	#	fnameD1 = 'synthetic_workload/W'+str(W)+'_D1'
		D0 = np.loadtxt(fnameD0, dtype='f', delimiter=',')
		D1 = np.loadtxt(fnameD1, dtype='f', delimiter=',')

		quantile = 0.95
		slo =  0.00003
		constraint = 'cost'
		sol = solveOptimizationProblem(D0, D1, model, quantile, slo, constraint)
		if constraint == 'latency':	
			print('---------- SLO on '+str(quantile*100)+'th latency = '+str(slo)+' s ----------')
		else:
			print('---------- SLO on '+str(quantile*100)+'th cost = '+str(slo)+' USD/request ----------')
		print('---------- Range: '+str(i-1)+'-'+str(i)+' ----------')
		print('Memory = '+str(sol[0])+' MB')
		print('Timeout = '+str(sol[1])+' s')
		print(str(quantile*100)+'th Latency = '+str(sol[2])+' s')
		print(str(quantile*100)+'th Cost = '+str(sol[3])+' USD/request')
		print('Solutions SLO compliant: '+str(sol[4])+' ('+str(float(sol[4]*100/sol[6]))+'%)')
		print('Optimal solutions: '+str(sol[5])+' ('+str(float(sol[5]*100/sol[6]))+'%)')



