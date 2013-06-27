# -*- coding: utf-8; py-indent-offset: 2 -*-

from __future__ import division
from libtbx import group_args
from libtbx.utils import Sorry
from math import exp
import os

# Brown, I. D., & Altermatt, D. (1985).
# Bond-valence parameters obtained from a systematic analysis
# of the Inorganic Crystal Structure Database.
# Acta Crystallographica Section B Structural Science,
# 41(4), 244-247. doi:10.1107/S0108768185002063

def cif_param_as_list (param) :
  if (param == ".") : return None
  return param.split(",")

def cif_param_as_int (param) :
  if (param == ".") : return None
  return int(param)

def cif_param_as_float (param) :
  if (param == ".") : return None
  return float(param)

class MetalParameters (group_args) :
  def __str__ (self) :
    return "%s%+d" % (self.element.upper(), self.charge)

  def charge_as_int (self) :
    return self.charge

  def scattering_type (self) :
    charge_symbol = ""
    if (self.charge > 0) :
      charge_symbol = "+"
    elif (self.charge < 0) :
      charge_symbol = "-"
    s = "%2s%1d%s" % (self.element.strip(), abs(self.charge), charge_symbol)
    return s

class server (object) :
  def __init__ (self) :
    import iotbx.cif
    params_path = os.path.join(os.path.split(__file__)[0],
      "ion_parameters.cif")
    assert (os.path.isfile(params_path))
    cif_model = iotbx.cif.reader(file_path=params_path).model()
    self.params = cif_model["ions"]
    self._metal_params = {}

  def is_supported_element (self, symbol) :
    return (symbol in self.params['_lib_valence.atom_symbol'])

  def is_supported_donor (self, symbol) :
    return (symbol in self.params['_lib_valence.donor_symbol'])

  def get_valence_params (self, atom1, atom2) :
    for i_elem, symbol in enumerate(self.params['_lib_valence.atom_symbol']) :
      if (symbol == atom1.element) :
        i_charge = int(self.params['_lib_valence.atom_charge'][i_elem])
        i_other = self.params['_lib_valence.donor_symbol'][i_elem]
        i_other_charge = int(self.params['_lib_valence.donor_charge'][i_elem])
        if ((i_charge == atom1.charge_as_int()) and
            (i_other == atom2.element) and
            (i_other_charge == atom2.charge_as_int())) :
          valence = float(self.params['_lib_valence.value'][i_elem])
          return valence, 0.37
    return None, None

  def get_metal_parameters (self, element) :
    p = self.params
    for i_elem, symbol in enumerate(p['_lib_elems.element']) :
      if (symbol == element.upper()) :
        if (symbol in self._metal_params) :
          return self._metal_params[symbol]
        assert (p['_lib_ligands.element'][i_elem] == symbol)
        params = MetalParameters(
          element=symbol,
          charge=cif_param_as_int(p['_lib_elems.charge'][i_elem]),
          vec_sum_cutoff=cif_param_as_float(
            p["_lib_elems.vec_sum_cutoff"][i_elem]),
          coord_num_lower=cif_param_as_int(
            p["_lib_elems.coord_num_lower"][i_elem]),
          coord_num_upper=cif_param_as_int(
            p["_lib_elems.coord_num_upper"][i_elem]),
          min_coordinating_non_waters=cif_param_as_int(
            p["_lib_elems.min_coordinating_non_waters"][i_elem]),
          cvbs_lower=cif_param_as_float(p['_lib_elems.cvbs_lower'][i_elem]),
          cvbs_upper=cif_param_as_float(p['_lib_elems.cvbs_upper'][i_elem]),
          cvbs_expected=cif_param_as_float(
            p['_lib_elems.cvbs_expected'][i_elem]),
          allowed_coordinating_atoms=cif_param_as_list(
            p['_lib_ligands.allowed_coordinating_atoms'][i_elem]),
          allowed_coordinating_residues=cif_param_as_list(
            p['_lib_ligands.allowed_coordinating_residues'][i_elem]),
          allowed_geometries=cif_param_as_list(
            p['_lib_ligands.allowed_geometries'][i_elem]),
          allowed_backbone_atoms=cif_param_as_list(
            p['_lib_ligands.allowed_backbone_atoms'][i_elem]))
        self._metal_params[symbol] = params
        return params
    return None

  def calculate_valence (self, ion, donor, distance):
    """
    Calculates the single valence contribution of one ion donor pair,
    separated by distance. ion and donor should be AtomGuess objects.
    """

    if (not self.is_supported_donor(donor.element)) :
      return 0

    r_0, b = self.get_valence_params(ion, donor)

    if (r_0 is None) :
      # Try again, this time using the default charge for the donor
      tmp = donor.charge
      donor.charge = default_charge(donor.element)
      r_0, b = self.get_valence_params(ion, donor)
      donor.charge = tmp

      if r_0 is None:
        return 0

    return exp((r_0 - distance) / b)

  def calculate_valences (self, ion, nearby_atoms):
    """
    Calculates all of the valence contributions between ion and each
    atom of nearby_atoms, each element of which should be a tuple of an
    atom and a vector from the ion's location.

    Returns a list of vectors, whose magnitudes are equal to the valence
    contributions from each donor atom.
    """

    vectors = []

    for contact in nearby_atoms:
      donor = AtomGuess(contact.element, contact.charge)
      distance = abs(contact.vector)
      valence = self.calculate_valence(ion, donor, distance) * contact.occ

      if valence == 0:
        if ((donor.element not in ["H", "C", "AX"]) and
            (not self.is_supported_donor(donor.element))) :
          pass
          #print "Unknown interaction: %s %s" % (ion.element, donor.element)
      elif distance != 0:
        #print contact.vector, contact.distance(), valence
        vectors.append(contact.vector / distance * valence)

    return vectors

# TODO move to ion_parameters.cif
CHARGES = {
  "H": -1,
  "LI": 1,
  "C": 4,
  "N": -3,
  "O": -2,
  "F": -1,
  "NA": 1,
  "MG": 2,
  "AL": 3,
  "SI": 4,
  "P": -3,
  "S": -2,
  "CL": -1,
  "K": 1,
  "CA": 2,
  "V": 3,
  "CR": 3,
  "MN": 2,
  "MN3": 3,
  "FE2": 2,
  "FE": 3,
  "CO": 2,
  "3CO": 3,
  "NI": 2,
  "3NI": 3,
  "CU1": 1,
  "CU": 2,
  "CU3": 3,
  "ZN": 2,
  "ZN2": 2,
  "ARS": 0,
  "SE": 2, # XXX: PDB has marked as charge of 0 (H2Se)
  "BR": -1,
  "RB": 1,
  "SR": 2,
  "Y1": 2,
  "YT3": 3,
  "MO": 0,
  "4MO": 4,
  "6MO": 6,
  "RU": 3,
  "PD": 2,
  "AG": 1,
  "CD": 2,
  "IN": 3,
  "I": -1,
  "CS": 1,
  "BA": 2,
  "W": 6,
  "RE": 0,
  "OS": 3,
  "OS4": 4,
  "IR3": 3,
  "IR": 4,
  "PT": 2,
  "PT4": 4,
  "AU": 1,
  "AU3": 3,
  "HG": 2,
  "TL": 1,
  "PB": 2,
  "BS3": 3,
  "AX": 0, # Dummy atom
}

class AtomGuess(object):
  def __init__(self, element, charge = None):
    self.element = element.upper()
    self.charge = charge if charge else default_charge(element)

  def charge_as_int (self) :
    return self.charge

  def __str__ (self) :
    return "%s%+d" % (self.element, self.charge)

  def scattering_type (self) :
    charge_symbol = ""
    if (self.charge > 0) :
      charge_symbol = "+"
    elif (self.charge < 0) :
      charge_symbol = "-"
    return "%s%d%s" % (self.element, self.charge, charge_symbol)

def get_element(atom):
  """
  Grabs an atom's element, stripping off whitespace and making sure the
  letters are capitalized.
  """
  return atom.element.strip().upper()

def get_charge(atom):
  if isinstance(atom, str):
    try:
      return default_charge(atom)
    except Sorry:
      return 0

  charge = atom.charge

  if not isinstance(charge, int):
    charge = atom.charge_as_int()

  if charge == 0:
    try:
      charge = default_charge(get_element(atom))
    except Sorry:
      return 0

  return charge

def default_charge(element):
  # Guess the charge state, may need to play around and try multiple when
  # guessing
  try:
    return CHARGES[element]
  except KeyError:
    raise Sorry("Unknown charge state for element: %s" % (element))

def compare_atom_weight(atom1, atom2):
  """
  Evaluates whether atom1 is lighter, heavier, or isoelectric to atom2, when
  atomic number and charge is taken into account.

  Returns -1 if lighter, 0 if isoelectric, and 1 if heavier.
  """
  from cctbx.eltbx import sasaki
  element1 = atom1.element.strip().upper()
  atom_num1 = sasaki.table(element1).atomic_number()
  charge1 = atom1.charge_as_int()

  if not charge1:
    charge1 = default_charge(element1)

  # Technically atom2 is a MetalParameter object, but it walks and talks
  # mostly like an atom
  element2 = atom2.element.strip().upper()
  atom_num2 = sasaki.table(element2).atomic_number()
  charge2 = int(atom2.charge)

  if not charge2:
    charge2 = default_charge(element2)

  return cmp(atom_num1 - charge1, atom_num2 - charge2)
