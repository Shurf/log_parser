def Hash(line):
	path= line.split("\"")[1]
	return path.split("\\")[5]

oldReadErrors = []
oldWriteErrors = []
oldDecompressErrors = []

oldInfected = set()
oldOK = set()
#------------------
newReadErrors = []
newWriteErrors = []
newDecompressErrors = []

newInfected = set()
newOK = set()

for logNumber in range(1,5):
	oldInfected.clear()
	oldOK.clear()
	newInfected.clear()
	newOK.clear()

	print "diffing logs #" + str(logNumber)
	oldLog = open("./old/" + str(logNumber) + ".log", "r")
	newLog = open("./new/" + str(logNumber) + ".log", "r")

	#process old log
	for oldLine in oldLog:
		#check for errors
		if ("\\virus\\samples\\" not in oldLine):
			continue
		oldHash = Hash(oldLine)

		if (" decompression error" in oldLine):
			if (not oldHash in oldDecompressErrors):
				oldDecompressErrors.append(oldHash)

		if (" read error" in oldLine):
			if (not oldHash in oldReadErrors):
				oldReadErrors.append(oldHash)

		if (" write error" in oldLine):
			if (not oldHash in oldWriteErrors):
				oldWriteErrors.append(oldHash)

		#check for detect
		if (oldHash in oldInfected):
			continue
		elif (oldHash not in oldOK):
			oldOK.add(oldHash)

		if (" infected with " in oldLine
			or" is adware program " in oldLine
			or " is hacktool program " in oldLine
			or " is riskware program" in oldLine
			or " is joke program" in oldLine):
			oldOK.remove(oldHash)
			oldInfected.add(oldHash)

	#process new log
	for newLine in newLog:
		#check for errors
		if ("\\virus\\samples\\" not in newLine):
			continue
		newHash = Hash(newLine)

		if (" decompression error" in newLine):
			if (not newHash in newDecompressErrors):
				newDecompressErrors.append(newHash)

		if (" read error" in newLine):
			if (not newHash in newReadErrors):
				newReadErrors.append(newHash)

		if (" write error" in newLine):
			if (not newHash in newWriteErrors):
				newWriteErrors.append(newHash)

		#check for detect
		if (newHash in newInfected or newHash in oldOK):
            #We should skip new detects and old OKs
			continue
		elif (newHash not in oldInfected and newHash not in oldOK):
            #completely new file in collection
			continue
		elif (newHash not in newOK):
			newOK.add(newHash)

		if (" infected with " in newLine
			or" is adware program " in newLine
			or " is hacktool program " in newLine
			or " is riskware program" in newLine
			or " is joke program" in newLine):
			newOK.remove(newHash)
			newInfected.add(newHash)

	outFile = open(str(logNumber) + ".ok.log", "w")
	for ok in newOK:
		outFile.write(ok)
		outFile.write("\n")
	outFile.close()
	print "Have " + str(len(newOK)) + " new OKs"

	oldLog.close()
	newLog.close()
