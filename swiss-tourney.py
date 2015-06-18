#!/usr/bin/python

import heapq
import sys
import re

def astar(start, h, c, trans, isFinal):
  q = [(c(start) + h(start), start)]
  heapq.heapify(q)
  seen = set([start])

  while True:
    (cost, s) = heapq.heappop(q)
    
    if isFinal(s):
      return s

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
  best = astar(start, h, c, trans, isFinal)

  return map(lambda matchup: tuple(map(lambda idx: standings[idx][0], matchup)), best)


def updateConstraints(constraints, games):
  for game in games:
    for i in xrange(len(game)-1):
      if game[i].startswith('bye'):
        continue
      for j in xrange(i+1, len(game)):
        if game[j].startswith('bye'):
          continue
        if (game[i],game[j]) in constraints or (game[j],game[i]) in constraints:
          continue
        constraints.add((game[i],game[j]))


def updateStandings(players, standings):
  pointsGainedPerPlayer = {}
  print 'Points gathered:'

  # For each player collect the number of points
  for i in xrange(len(players)):
    pts = raw_input("\n\t" + players[i] + ": ")
    while True:
      if re.match('\d+$', pts.strip()):
        break
      print "\n\t\tYour selection '" + pts + "' is not a number. Please enter again."
      pts = raw_input("\t"+ players[i] + ": ")

    pointsGainedPerPlayer[players[i]] = int(pts.strip())


  standings = map(lambda x: (x[0], x[1]+pointsGainedPerPlayer[x[0]]), standings)
  standings = sorted(standings,key=lambda x: x[1], reverse=True)
  return standings


def printGames(games):
  count = 0;
  for game in games:
    count += 1
    print 'Game ' + str(count)
    for playerID in game:
      print '\t' + playerID


def printStandings(standings):
  print '\nCurrent Results:'
  for standing in standings:
    print '\t' + standing[0] + ' --> ' + str(standing[1])


def main():

  players =  []
  numberOfPlayers = int(raw_input("Number of players: "))
  for i in xrange(numberOfPlayers):
    players.append(raw_input("\tPlayer " + str(i+1) + ": "))

  playersPerGame = int(raw_input("\nNumber of players per game: "))

  numberOfByePlayers = 0
  if len(players) % playersPerGame != 0:
    for i in xrange(playersPerGame - len(players) % playersPerGame):
      numberOfPlayers += 1
      numberOfByePlayers += 1
      players.append('bye' + str(i+1))
  numberOfGames = len(players) / playersPerGame

  standings = map(lambda x: tuple([x,0]), players)

  constraints = set()
  for i in xrange(numberOfByePlayers-1):
    constraints.add(('bye' + str(i+1),'bye' + str(i+2)))

  numberOfRounds = int(raw_input("\nNumber of rounds: "))

  for n in xrange(numberOfRounds):
    print '----- Round ' + str(n+1) + ' -----'
    games = getNextRoundGames(standings, constraints, playersPerGame, numberOfGames)
    printGames(games)
    updateConstraints(constraints, games)
    standings = updateStandings(players, standings)
    printStandings(standings)

if __name__ == '__main__':
  main()
