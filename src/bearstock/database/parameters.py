
from typing import Any, Dict, Optional, Union

import copy

from .errors import BearDatabaseError, BearModelError
from .model import Model
from .product import Product


class Parameters(Model):

    def __init__(self, *,
                 uid: Optional[int] = None,
                 timestamp: Optional[int] = None,
                 parameters: Optional[Dict[str, Any]] = None,
                 database: Optional['Database'] = None) -> None:
        super().__init__(database=database)

        self._uid = uid
        self._timestamp = timestamp
        self._parameters = parameters

    @property
    def uid(self) -> Optional[int]:
        """Parameters id."""
        return self._id

    @property
    def timestamp(self) -> Optional[int]:
        """Timestamp parameters was created."""
        return self._timestamp

    @property
    def parameters(self) -> Optional[Dict[str, Any]]:
        """Full parameter blob."""
        return self._parameters
    @parameters.setter
    def parameters(self, parameters: Dict[str, Any]) -> None:
        self._parameters = parameters

    def _retreive_product(self, product: Union[str, 'Product']) -> Product:
        if isinstance(product, str):
            product = self._database.get_product(product)
        elif isinstance(product, Product):
            if not product.is_bound():
                product = self._database.get_product(product.code)
        else:
            raise ValueError('product is not a product or string (product code)')

        return product

    def get_params_for_product(self, product: Union[str, 'Product']) -> Dict[str, Any]:
        """Get parameters for a product or a product code.

        Raises:
            BearModelError: If the parameters have no parmeter data.
            ValueError: If ``product`` is not a string (product code) or a product instance.
        """
        if self.parameters is not None:
            raise BearModelError('no parameter data')

        product = self._retreive_product(product)

        params = copy.deepcopy(self._parameters[None])  # copy default parameters
        if product.code in self.parameters:
            product_dict = self.parameters[product.code]
            for key, el in product_dict.items():
                params[key] = el

        return params

    def set_product_parameter(self, product: Union[str, 'Product'], value: Any) -> None:
        """Get parameters for a product or a product code.

        Raises:
            BearModelError: If the parameters have no parmeter data.
            ValueError: If ``product`` is not a string (product code) or a product instance.
        """
        if self.parameters is not None:
            raise BearModelError('no parameter data')

        product = self._retreive_product(product)

        if product.code not in self.parameters:
            self.parameters[product.code] = {}

        self.parameters[product.code] = value

    def as_dict(self) -> Dict[str, Any]:
        """Return the parameters instance as a dictionary.

        This method is for interoperability with the web server parts of BearStock.
        The fields in the dictionary are: ``id``, ``timestamp``, ``parmeters``.
        """
        last_order = self.last_order
        return dict(
            id=self.uid,
            timestamp=self._timestamp,
            parameters=copy.deepcopy(self._parameters),
        )

    def synchronize(self) -> None:
        """Reload to parameters."""
        if not self.is_bound():
            raise BearModelError('parameters not bound')

        parmeters = self.get_db().get_parameters(self.uid)

        self._timestamp = parameters.timestamp
        self._parameters = parameters.parameters

    def insert_into(self, db: 'Database', *, rebind: bool = False) -> None:
        if self.is_bound() and not rebind:
            raise BearModelError('parameters already bound to a database')
        if db is None or not db.is_connected():
            raise ValueError('database None or not connected')

        self._database = db
        self._uid = None

        # may raise BearDatabaseError
        inserted = db.insert_parameters(
                timestamp=self.timestamp, parameters=self.parameters)
        self._database = db

        self._uid = inserted.uid

    def update_in_db(self) -> None:
        if self.is_bound() is None:
            raise BearModelError('parameters not bound to a database')

        # may raise BearDatabaseError
        self._database.update_parameters(self)

    @classmethod
    def load_from_db(cls, db: 'Database', uid: int) -> 'Parmeters':
        if db is None:
            raise ValueError('database is None')
        if not db.is_connected():
            raise ValueError('database not connected')

        # may throw BearDatabaseError
        parameters = db.get_parameters(uid)

        if parameters is None:
            raise ValueError(f'no parameters with id: {uid}')

        return parameters

