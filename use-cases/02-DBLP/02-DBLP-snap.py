"""
 Use case #2: create a coauthorship network and get the table of authors sorted by PageRank score
"""

import sys
sys.path.append("..")
sys.path.append("../../ringo-engine-python")
import os
import time
import snap
import testutils

N_TOP_AUTHORS = 20
ENABLE_TIMER = True
OUTPUT_TABLE_FILENAME = 'table.tsv'
PAGE_RANK_ATTRIBUTE = "PageRank"
NODE_ATTR_NAME = "__node_attr"

if len(sys.argv) < 2:
  print """Usage: python 02-DBLP-snap.py source [destination]
  source: input DBLP .tsv file
  destination: output .tsv file containing PageRank scores"""
  exit(1)
srcfile = sys.argv[1]
dstdir = sys.argv[2] if len(sys.argv) >= 3 else None
if not dstdir is None:
  try:
    os.makedirs(dstdir)
  except OSError:
    pass

context = snap.TTableContext()

t = testutils.Timer(ENABLE_TIMER)

# Load data
# >>> authors = ringo.load('authors.tsv')
S = snap.Schema()
S.Add(snap.TStrTAttrPr("Key", snap.atStr))
S.Add(snap.TStrTAttrPr("Author", snap.atStr))
T = snap.TTable.LoadSS("1", S, srcfile, context, '\t', snap.TBool(False))
t.show("load")

# Self-join
# >>> authors.selfjoin(authors, ['Key'])
T = T.SelfJoin("Key")
t.show("join")

# Select
# >>> authors.select('Author_1 != Author_2')
T.SelectAtomic("1_1.Author", "1_2.Author", snap.NEQ)
t.show("select")

# Create network
# >>> authors.graph('Author_1', 'Author_2', directed=False)
# TODO: Bug - what if a node only appears in the destination column ? (symmetric in our case)
T.SetSrcCol("1_1.Author")
T.SetDstCol("1_2.Author")
G = T.ToGraph(snap.aaFirst)
t.show("graph")

# Compute PageRank score
# >>> graph.pageRank('PageRank')
HT = snap.TIntFltH()
snap.GetPageRank(G, HT)
P = snap.TTable("PR", HT, "Author", "PageRank", context, snap.TBool(True))
t.show("page rank")

# Order by PageRank score (in descending order)
# >>> rank.order(['PageRank'], desc = True)
V = snap.TStrV()
V.Add(PAGE_RANK_ATTRIBUTE)
P.Order(V, "", snap.TBool(False), snap.TBool(False))
t.show("order")

# Save final table
# >>> rank.save('table.tsv')
if not dstdir is None:
  P.SaveSS(os.path.join(dstdir,OUTPUT_TABLE_FILENAME))
  t.show("save")

# Print top authors with their PageRank score
testutils.dump(P, N_TOP_AUTHORS)