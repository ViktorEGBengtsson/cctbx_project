from __future__ import division, print_function
'''
'''

import iotbx.pdb
import mmtbx.model

from iotbx.file_reader import any_file
from libtbx.data_manager import DataManagerBase
from libtbx.utils import Sorry

# =============================================================================
class ModelDataManager(DataManagerBase):

  datatype = 'model'

  # ---------------------------------------------------------------------------
  # Models
  def add_model(self, filename, data):
    return self._add(ModelDataManager.datatype, filename, data)

  def set_default_model(self, filename):
    return self._set_default(ModelDataManager.datatype, filename)

  def get_model(self, filename=None):
    return self._get(ModelDataManager.datatype, filename)

  def get_model_names(self):
    return self._get_names(ModelDataManager.datatype)

  def get_default_model_name(self):
    return self._get_default_name(ModelDataManager.datatype)

  def remove_model(self, filename):
    return self._remove(ModelDataManager.datatype, filename)

  def has_models(self, expected_n=1, exact_count=False, raise_sorry=False):
    return self._has_data(ModelDataManager.datatype, expected_n=expected_n,
                          exact_count=exact_count, raise_sorry=raise_sorry)

  def process_model_file(self, filename):
    # unique because any_file does not return a model object
    if (filename not in self.get_model_names()):
      a = any_file(filename)
      if (a.file_type != 'pdb'):
        raise Sorry('%s is not a recognized model file' % filename)
      else:
        model_in = iotbx.pdb.input(a.file_name)
        model = mmtbx.model.manager(model_input=model_in)
        self.add_model(filename, model)

# =============================================================================
# end