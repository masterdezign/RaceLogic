""" 
    Python 2.7 
    
    Flat Race Tree:
    A decision trees can be viewed as a set of independent and parallel rather than 
    sequential decision rules that lead to a final prediction when combined accordingly. 
    Each leaf now can be represented as a logical function of the binary decisions 
    encountered at the nodes on its path to the root. In other words, each path from 
    the tree root to a leaf corresponds to a unique conjunction of attribute tests.
   
    Reference: 
    G. Tzimpragos, A. Madhavan, D. Vasudevan, D. Strukov, and T. Sherwood, 
    "Boosted Race Trees for Low Energy Classification", in the 24th International 
    Conference on Architectural Support for Programming Languages and Operating 
    Systems (ASPLOS), Providence, RI, 2019.

    More about PyRTL: https://pyrtl.readthedocs.io/
"""

import pyrtl
import math
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'base'))
from racelogic_primitives import inhibit_rl 

class FlatRaceTree:
    
    def __init__(self, inp_res, tree_depth, attributes, tree_nodes):
        self.inp_res = inp_res
        self.tree_depth = tree_depth
        self.attributes = attributes
        self.tree_nodes = tree_nodes
        return 

    def decoder(self, din):
        """
            Read the output of the inhibits' array and translate it into
            an 1-hot encoded vector and then into its binary equivalent.
        """
        tmp = [[None for x in range(self.tree_depth)] for y in range(2**self.tree_depth)]
        step = 2**self.tree_depth
        idx = 0
        for i in range(self.tree_depth):
            for j in range(2**self.tree_depth):
                if (j%step == 0):
                    idx += 1
                if (j//(step/2))%2:
                    tmp[j][i] = ~ din[idx-1]
                else:
                    tmp[j][i] = din[idx-1]
            step = step/2
        dec_1hot = [and_rec(tmp[j]) for j in range(2**self.tree_depth)]
        dec_bin = onehot2bin(dec_1hot)
        return dec_bin

    def tree(self):
        """
            Construct a Flat Race Tree.
        """
        # create a local copy of the input feature data (tree's attributes)
        a = data_buffer(self.attributes)
        # create delay-coded thresholds
        t = shift_reg(din = pyrtl.Const("1'b1"), n = 2**self.inp_res - 1)
        # connect attributes and thresholds to the inhibits implementing tree's nodes
        tree_inhs_o = [inhibit_rl(t[self.tree_nodes[i][0]], a[self.tree_nodes[i][1]]) for i in range(len(self.tree_nodes))]
        # decode
        dec_bin = self.decoder(tree_inhs_o)
        valid_out = t[-1]
        out = (dec_bin, valid_out)
        return out


### Auxiliary "functions" ###

def shift_reg(din, n):
    """
        Use a shift register to create delay-coded thresholds.
    """
    sr = pyrtl.Register(bitwidth = n)
    sr.next <<= pyrtl.concat(sr[:-1], din)
    return sr

def data_buffer(din):
    """
        Create a data buffer.
    """
    dt_buffer = pyrtl.Register(bitwidth = len(din))
    dt_buffer.next <<= din
    return dt_buffer

def onehot2bin(din):
    """
        1-hot to binary encoder.
    """
    bin_l = [None]* len(din)
    for i in range(len(din)):
        b = pyrtl.WireVector(int(math.log(len(din),2)))
        with pyrtl.conditional_assignment:
            with din[i]:
                b |= i
            with pyrtl.otherwise:
                b |= 0
        bin_l[i] = b
    dout = or_rec(bin_l)
    return dout

def or_rec(din_l):
    """
        ORing a list of WireVectors recursively.
    """
    if len(din_l) == 1:
        dout = din_l[0]
    else:
        dout = din_l[0] | or_rec(din_l[1:])
    return dout

def and_rec(din_l):
    """
        ANDing a list of WireVectors recursively.
    """
    if len(din_l) == 1:
        dout = din_l[0]
    else:
        dout = din_l[0] & or_rec(din_l[1:])
    return dout
