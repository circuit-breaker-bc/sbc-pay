# Copyright © 2024 Province of British Columbia
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Model to handle all operations related to Credit data."""
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, func

from .base_model import BaseModel
from .db import db, ma


class Credit(BaseModel):
    """This class manages all of the base data about Credit."""

    __tablename__ = "credits"
    # this mapper is used so that new and old versions of the service can be run simultaneously,
    # making rolling upgrades easier
    # This is used by SQLAlchemy to explicitly define which fields we're interested
    # so it doesn't freak out and say it can't map the structure if other fields are present.
    # This could occur from a failed deploy or during an upgrade.
    # The other option is to tell SQLAlchemy to ignore differences, but that is ambiguous
    # and can interfere with Alembic upgrades.
    #
    # NOTE: please keep mapper names in alpha-order, easier to track that way
    #       Exception, id is always first, _fields first
    __mapper_args__ = {
        "include_properties": [
            "id",
            "account_id",
            "amount",
            "cfs_identifier",
            "cfs_site",
            "created_on",
            "details",
            "is_credit_memo",
            "remaining_amount",
            "created_invoice_id",
        ]
    }

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    cfs_identifier = db.Column(db.String(50), nullable=True, index=True)
    # Indicates which payment method the credit is associated with, so we know to put it in ob_credit or pad_credit
    cfs_site = db.Column(db.String(50), ForeignKey("cfs_accounts.cfs_site"), nullable=True)
    is_credit_memo = db.Column(Boolean(), default=False)
    amount = db.Column(db.Float, nullable=False)
    remaining_amount = db.Column(db.Float, nullable=False)
    details = db.Column(db.String(200), nullable=True)
    created_on = db.Column(
        "created_on",
        db.DateTime,
        nullable=True,
        default=lambda: datetime.now(tz=timezone.utc),
    )
    created_invoice_id = db.Column(db.Integer, ForeignKey("invoices.id"), nullable=True, index=True)
    account_id = db.Column(db.Integer, ForeignKey("payment_accounts.id"), nullable=True, index=True)

    @classmethod
    def find_by_cfs_identifier(cls, cfs_identifier: str, credit_memo: bool = False):
        """Find Credit by cfs identifier."""
        return cls.query.filter_by(cfs_identifier=cfs_identifier).filter_by(is_credit_memo=credit_memo).one_or_none()

    @classmethod
    def find_remaining_by_account_id(cls, account_id: int) -> Decimal:
        """Find Credit by account id."""
        return Decimal(
            str(
                cls.query.with_entities(func.coalesce(func.sum(Credit.remaining_amount), 0))
                .filter_by(account_id=account_id)
                .scalar()
            )
        )


class CreditSchema(ma.SQLAlchemyAutoSchema):  # pylint: disable=too-many-ancestors
    """Main schema used to serialize the Credit."""

    class Meta:  # pylint: disable=too-few-public-methods
        """Returns all the fields from the SQLAlchemy class."""

        model = Credit
        load_instance = True
