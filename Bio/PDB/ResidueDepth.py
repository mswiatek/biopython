from Numeric import array, sum, sqrt
import tempfile
import os
import sys

from Bio.PDB import *


__doc__="""
Calculation of residue depth (using Michel Sanner's MSMS program for the
surface calculation).

Residue depth is the average distance of the atoms of a residue from 
the solvent accessible surface.

Residue Depth:

    rd=ResidueDepth(model, pdb_file)

    print rd[residue]

    Each Residue object is mapped to a (residue depth, ca depth) 
    tuple.

Direct MSMS interface:

    Typical use:

        surface=get_surface("1FAT.pdb")

    Surface is a Numpy array with all the surface 
    vertices.  

    Distance to surface:

        dist=min_dist(coord, surface)

    where coord is the coord of an atom within the volume
    bound by the surface (ie. atom depth).

    To calculate the residue depth (average atom depth
    of the atoms in a residue):

    rd=residue_depth(residue, surface)
"""

def _read_vertex_array(filename):
    """
    Read the vertex list into a Numpy array.
    """
    fp=open(filename, "r")
    vertex_list=[]
    for l in fp.readlines():
        sl=l.split()
        if not len(sl)==9:
            # skip header
            continue
        vl=map(float, sl[0:3])
        vertex_list.append(vl)
    fp.close()
    return array(vertex_list)

def get_surface(pdb_file, PDB_TO_XYZR="pdb_to_xyzr", MSMS="msms"):
    """
    Return a Numpy array that represents 
    the vertex list of the molecular surface.

    PDB_TO_XYZR --- pdb_to_xyzr executable (arg. to os.system)
    MSMS --- msms executable (arg. to os.system)
    """
    # extract xyz and set radii
    xyz_tmp=tempfile.mktemp()
    PDB_TO_XYZR=PDB_TO_XYZR+" %s > %s"
    make_xyz=PDB_TO_XYZR % (pdb_file, xyz_tmp) 
    os.system(make_xyz)
    # make surface
    surface_tmp=tempfile.mktemp()
    MSMS=MSMS+" -probe_radius 1.5 -if %s -of %s > "+tempfile.mktemp()
    make_surface=MSMS % (xyz_tmp, surface_tmp)
    os.system(make_surface)
    surface_file=surface_tmp+".vert"
    # read surface vertices from vertex file
    surface=_read_vertex_array(surface_file)
    # clean up tmp files
    # ...this is dangerous
    #os.system("rm "+xyz_tmp)
    #os.system("rm "+surface_tmp+".vert")
    #os.system("rm "+surface_tmp+".face")
    return surface


def min_dist(coord, surface):
    """
    Return minimum distance between coord
    and surface.
    """
    d=surface-coord
    d2=sum(d*d, 1)
    return sqrt(min(d2))

def residue_depth(residue, surface):
    """
    Return average distance to surface for all
    atoms in a residue, ie. the residue depth.
    """
    atom_list=residue.get_unpacked_list()
    length=len(atom_list)
    d=0
    for atom in atom_list:
        coord=atom.get_coord()
        d=d+min_dist(coord, surface)
    return d/length

def ca_depth(residue, surface):
    if not residue.has_id("CA"):
        return -1
    ca=residue["CA"]
    coord=ca.get_coord()
    return min_dist(coord, surface)

class ResidueDepth:
    """
    Calculate residue and CA depth for all residues.
    """
    def __init__(self, model, pdb_file):
        depth_dict={}
        depth_list=[]
        # get_residue
        residue_list=Selection.unfold_entities(model, 'R')
        # make surface from PDB file
        surface=get_surface(pdb_file)
        # calculate rdepth for each residue
        for residue in residue_list:
            rd=residue_depth(residue, surface)
            ca_rd=ca_depth(residue, surface)
            depth_dict[residue]=(rd, ca_rd)
            depth_list.append((residue, (rd, ca_rd)))
        self.depth_list=depth_list
        self.depth_dict=depth_dict

    def __getitem__(self, key):
        """
        Map (chain_id, res_id) to (residue depth, CA depth) tuple.
        """
        return self.depth_dict[key]

    def __len__(self):
        return len(self.depth_list)

    def has_key(self, res):
        return self.depth_dict.has_key(res)

    def get_iterator(self):
        """
        Loop over list of ((chain_id, res_id), (residue depth, CA depth))
        tuples.
        """
        for i in range(0, len(self.depth_list)):
            yield self.depth_list[i] 


if __name__=="__main__":

    import sys

    p=PDBParser()
    s=p.get_structure("X", sys.argv[1])
    model=s[0]

    rd=ResidueDepth(model, sys.argv[1])


    for item in rd.get_iterator():
        print item
