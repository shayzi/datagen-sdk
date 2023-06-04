import numpy as np
from marshmallow.fields import Field
from marshmallow_dataclass import NewType


class _NumpyArray(Field):
    def _deserialize(self, value, *args, **kwargs):
        if isinstance(value, dict):
            if self._is_numeric_keys(value):
                value = self._extract_from_numeric_keys(value)
            else:
                value = self._extract_from_xyz_keys(value)
        return np.array(value)

    def _is_numeric_keys(self, value: dict) -> bool:
        return all(map(lambda key: key.isnumeric(), value.keys()))

    def _extract_from_numeric_keys(self, dict_: dict) -> list:
        list_ = []
        for idx in self._get_sorted_indexes(dict_):
            list_.append(dict_[str(idx)])
        return list_

    def _extract_list(self, dict_) -> list:
        try:
            return self._extract_from_xyz_keys(dict_)
        except KeyError:
            return self._extract_from_numeric_keys(dict_)

    def _extract_from_xyz_keys(self, dict_: dict) -> list:
        list_ = [dict_["x"], dict_["y"]]
        if "z" in dict_:
            list_.append(dict_["z"])
        return list_

    def _get_sorted_indexes(self, dict_) -> list:
        return sorted(int(s) for s in dict_.keys())


NumpyArray = NewType("NdArray", np.ndarray, field=_NumpyArray)
