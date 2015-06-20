##### This only works with python2

import heapq
import sys
import re
import time
import os
import threading
from multiprocessing import Process

# global for logfile
recordFile = ''
gameStatusFile = ''

def astar(start, h, c, trans, isFinal):
  startCost = c(start) + h(start)
  q = [(startCost, start)]
  heapq.heapify(q)

  seen = set([start])

  bestSoFar = start
  bestSoFarCost = c(start) + h(start)
  bestSoFarLength = len(start)

  while True:
    if not q:
      return (bestSoFar, False)

    (cost, s) = heapq.heappop(q)
    
    if isFinal(s):
      return (s, True)

    if len(s) > bestSoFarLength or (len(s) is bestSoFarLength and  cost < bestSoFarCost):
      bestSoFar = s
      bestSoFarCost = cost
      bestSoFarLength = len(s)

    newstates = trans(s)
    for new in newstates:
      if not new in seen:
        seen.add(new)
        heapq.heappush(q, (c(new) + h(new), new))


def cost(state, standings):
  c = 0
  for matchup in state:
    for i in xrange(len(matchup)-1):
      c += standings[matchup[i]][1] - standings[matchup[i+1]][1]
  return c


def heuristic(state, standings, playersPerGame):
  h = 0
  addedIdxs = set()
  for matchup in state:
    for i in xrange(len(matchup)):
      addedIdxs.add(matchup[i])

  rankList = []
  for i in xrange(len(standings)):
    if not i in addedIdxs:
      rankList.append(standings[i][1])

  for i in xrange(0, len(rankList), playersPerGame):
    for j in xrange(i, i+playersPerGame-1):
      h += rankList[j] - rankList[j+1]

  return h


def isFinalState(state, numberOfGames):
  if len(state) < numberOfGames:
    return False
  return True


def generateNextStates(state, possibleMatchups):
  allowedMatchups = set()
  for matchup in possibleMatchups:
    allowed = True
    for stateMatchup in state:
      for i in matchup:
        if i in stateMatchup:
          allowed = False
          break
      if not allowed:
        break
    if allowed:
      allowedMatchups.add(matchup)

  return map(lambda newMatchup: state | frozenset([newMatchup]), allowedMatchups)


def getPossibleMatchups(standings, constraints, playersPerGame):
  matchups = []

  for i in xrange(len(standings)):
    (playerID, points) = standings[i]
    matchups.append(tuple([i]))

  currentPlayers = 1
  while currentPlayers < playersPerGame:
    newMatchups = []
    for i in xrange(len(matchups)):
      matchup = matchups[i]
      lastPlayerIdx = matchup[currentPlayers-1]
      for j in xrange(lastPlayerIdx+1, len(standings)):
        potentialPlayerID = standings[j][0]
        canAddPlayer = True
        for b in xrange(len(matchup)):
          playerIdx = matchup[b]
          playerID = standings[playerIdx][0]
          if (playerID, potentialPlayerID) in constraints or (potentialPlayerID, playerID) in constraints:
            canAddPlayer = False
            break
        if canAddPlayer:
          newMatchups.append(matchup + (j,))
    matchups = newMatchups
    currentPlayers += 1
  return matchups


def getNextRoundGames(standings, constraints, playersPerGame, numberOfGames):
  possibleMatchups = getPossibleMatchups(standings, constraints, playersPerGame)

  start = frozenset()
  h = lambda state: heuristic(state, standings, playersPerGame)
  c = lambda state: cost(state, standings)
  trans = lambda state: generateNextStates(state, possibleMatchups)
  isFinal = lambda state: isFinalState(state, numberOfGames)

  (best, Completed) = astar(start, h, c, trans, isFinal)
  while not Completed:
    unassignedPlayers = set(map(lambda (pl,pts): pl, standings))
    for matchup in best:
      for idx in matchup:
        unassignedPlayers.remove(standings[idx][0])

#    print('\nStuck with these games:')
#    printGames(map(lambda matchup: tuple(map(lambda idx: standings[idx][0], matchup)), best))

#    print('\nUnassigned players:' + str(list(unassignedPlayers)))


    relevantConstraintsList = filter(lambda (pl0,pl1): pl0 in unassignedPlayers and pl1 in unassignedPlayers and not (pl0.startswith('bye') and pl1.startswith('bye')), constraints)
    if not relevantConstraintsList:
       raise ValueError('releveant cpnstraints empty')

#    print('\nRemoving relevant constraints:')
#    printConstraintsList(relevantConstraintsList)

    constraints -= set(relevantConstraintsList)

#    print('\nRetrying:')

    possibleMatchups = getPossibleMatchups(standings, constraints, playersPerGame)
    start = frozenset()
    trans = lambda state: generateNextStates(state, possibleMatchups)
    (best, Completed) = astar(start, h, c, trans, isFinal)

  return map(lambda matchup: tuple(map(lambda idx: standings[idx][0], matchup)), best)


def updateConstraints(constraints, games):
  for game in games:
    for i in xrange(len(game)-1):
      #if game[i].startswith('bye'):
      #  continue
      for j in xrange(i+1, len(game)):
        #if game[j].startswith('bye'):
        #  continue
        if (game[i],game[j]) in constraints or (game[j],game[i]) in constraints:
          continue
        constraints.add((game[i],game[j]))

def checkStandingsInput(players, pointsGainedPerPlayer):

  ptsCorrect = ''

  while True:
    # Ask if the point selection is correct
    print("\n\n\tYou entered the following points: ")
    for i in xrange(len(players)):
      print("\t\t" + players[i] + ": " + str(pointsGainedPerPlayer[players[i]]))
    done = rec_raw_input("\tIs this correct: [y/n] ")

    # Hit enter without choice or choice was not y/n
    while done != 'y' and done != 'n':
      done = rec_raw_input("\n\t\tYou did not select 'y' or 'n' please try again: [y/n]")

    if done == 'y':
      break

    # If they need to update a player, loop for players to update
    while done != 'y':
      player = rec_raw_input("\n\tWhich player has an incorrect points? ")
      newpts = rec_raw_input("\n\tEnter the new points for " + player + ": ")
      print("\n\tModifying " + player + "'s " + "points to: " + newpts)
      pointsGainedPerPlayer[player] = newpts
      done = rec_raw_input("\t\tAre you done modifying player points? [y/n]")

  return pointsGainedPerPlayer

def updateStandings(players, standings):
  pointsGainedPerPlayer = {}
  print('\tPoints gathered:')

  i = 0
  while i < len(players):

    # Ask which game is done
    player = rec_raw_input('\tUpdate points for what player? ')

    while(player not in players): 
      player = rec_raw_input("Player is not playing.  Try again: ")

    pts = rec_raw_input("\n\tPoints earned by " + player + ": ")
    while True:
      if re.match('\d+$', pts.strip()):
        break
      print("\n\t\tYour selection '" + pts + "' is not a number. Please enter again.")
      pts = rec_raw_input("\t"+ player + ": ")

    pointsGainedPerPlayer[player] = int(pts.strip())
    i += 1

  # For each player collect the number of points
  #for i in xrange(len(players)):
    #pts = rec_raw_input("\n\t" + players[i] + ": ")
    #while True:
    #  if re.match('\d+$', pts.strip()):
    #    break
    #  print("\n\t\tYour selection '" + pts + "' is not a number. Please enter again.")
    #  pts = rec_raw_input("\t"+ players[i] + ": ")
    #pointsGainedPerPlayer[players[i]] = int(pts.strip())

  # Validate points 
  pointsGainedPerPlayer = checkStandingsInput(players, pointsGainedPerPlayer)

  # TODO: Check for point distribution for correct values

  standings = map(lambda x: (x[0], x[1]+int(pointsGainedPerPlayer[x[0]])), standings)
  standings = sorted(standings,key=lambda x: x[1], reverse=True)
  return standings

def printGames(games):
  global gameStatusFile
  count = 0;
  for game in games:
    count += 1
    print('\tGame ' + str(count))
    gameStatusFile.write('\n\tGame ' + str(count))
    for playerID in game:
      print('\t\t' + playerID)
      gameStatusFile.write('\n\t\t' + playerID)
  gameStatusFile.flush()


def printStandings(standings):
  global gameStatusFile
  print('\n\tCurrent Results:')
  gameStatusFile.write('\n\tCurrent Results:')
  for standing in standings:
    print('\t\t' + standing[0] + ' --> ' + str(standing[1]))
    gameStatusFile.write('\n\t\t' + standing[0] + ' --> ' + str(standing[1]))
  gameStatusFile.flush()

def printConstraintsList(constraintsList):
  global gameStatusFile
  count = 0;
  for constraint in constraintsList:
    count += 1
    print('\tConstraint ' + str(count) + ': ' + constraint[0] + ' not in the same table as ' + constraint[1])

def rec_raw_input(inStr):
  global recordFile
  input = raw_input(inStr)
  recordFile.write(input+"\n")
  recordFile.flush()
  return input

def statusFileOpen():
  # File for current statndings and match organization 
  global gameStatusFile
  gStatusDirname = "/usr/share/nginx/html/dominion"

  try:
    os.mkdir(gStatusDirname)
  except Exception:
    # TODO: fix this to be more flexible
    print "You must create the dominion directory: " + gStatusDirname

  statsFname = "game_status." + str(time.time())
  statsFP = gStatusDirname + '/' + statsFname
  currGameFP = gStatusDirname + '/game.txt'
  gameStatusFile = open(statsFP, 'w')
  try:
    os.unlink(currGameFP)
  except Exception:
    pass
  os.symlink(statsFP, currGameFP)

def webServerStart():
  os.popen("cd /tmp/swisstourney && python2 -m SimpleHTTPServer 8080")
  #os.system("cd /tmp/swisstourney && python2 -m SimpleHTTPServer 8080 2>&1")

def main():

  # record user input for state saving
  global recordFile
  recordFile = open('/tmp/game_record.'+str(time.time()), 'w')

  statusFileOpen()
  #t = threading.Thread(target=webServerStart, args=())
  #t = Process(target=webServerStart, args=())
  #t.daemon = True
  #t.start()

  players =  []

  # read names from file if desired 
  if rec_raw_input("\nWould you like to read players from a file (default: n)? [y/n] ") == 'y':
    playerFileStr = rec_raw_input("Path to file with the player names? ")
    playerFile = open(playerFileStr,'r')
    for line in playerFile:
      players.append(line.strip())
      print "\tAdding player: " + line.strip()
  else:
    numberOfPlayers = int(rec_raw_input("Number of players: "))
    for i in xrange(numberOfPlayers):
      players.append(rec_raw_input("\tPlayer " + str(i+1) + ": "))
  
  # Print out the players playing
  gameStatusFile.write('\n<<<< Players >>>>')
  for p in players:
    gameStatusFile.write('\n\tPlayer: ' + p)
  gameStatusFile.flush()

  playersPerGame = int(rec_raw_input("\nNumber of players per game: "))
  numberOfByePlayers = 0
  if len(players) % playersPerGame != 0:
    for i in xrange(playersPerGame - len(players) % playersPerGame):
      numberOfPlayers += 1
      numberOfByePlayers += 1
      players.append('bye' + str(i+1))

  numberOfGames = len(players) / playersPerGame

  standings = map(lambda x: tuple([x,0]), players)

  constraints = set()
  for i in xrange(numberOfByePlayers):
    for j in xrange(i+1, numberOfByePlayers):
      constraints.add(('bye' + str(i+1),'bye' + str(j+1)))
  numberOfRounds = int(rec_raw_input("\nNumber of rounds: "))

  for n in xrange(numberOfRounds):
    print('\n\n----- Round ' + str(n+1) + ' -----')
    gameStatusFile.write('\n\n----- Round ' + str(n+1) + ' -----')
    games = getNextRoundGames(standings, constraints, playersPerGame, numberOfGames)
    printGames(games)
    updateConstraints(constraints, games)
    standings = updateStandings(players, standings)
    printStandings(standings)

  print("\n****** Final swiss round results:")
  gameStatusFile.write("\n\n****** Final swiss round results:")
  printStandings(standings)
  gameStatusFile.flush()

  #answer = rec_raw_input("Stop running server now? [y/N]: ")
  #time.sleep(10)
  #t.terminate()
  #while True:
  #  if answer in [ "Y", "y" ]:
  #      #os.popen("kill -9 "+str(t))
  #      break
  #  # Do something here - maybe cleanup?
  #  # Terminate gracefully

if __name__ == '__main__':
  main()
