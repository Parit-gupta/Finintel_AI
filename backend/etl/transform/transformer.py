from backend.etl.transform.generic_rules import apply_generic_rules

from backend.etl.transform.transform_accounts import transform_accounts
from backend.etl.transform.transform_banking_products import (
    transform_banking_products
)
from backend.etl.transform.transform_branch_performance import (
    transform_branch_performance
)
from backend.etl.transform.transform_branches import transform_branches
from backend.etl.transform.transform_credit import (
    transform_german_credit,
    transform_credit_score
)
from backend.etl.transform.transform_customers import transform_customers
from backend.etl.transform.transform_employees import transform_employees
from backend.etl.transform.transform_fraud import (
    transform_credit_card_fraud
)
from backend.etl.transform.transform_loans import transform_loans
from backend.etl.transform.transform_marketing_campaigns import (
    transform_marketing_campaigns
)
from backend.etl.transform.transform_prediction_history import (
    transform_prediction_history
)
from backend.etl.transform.transform_support_tickets import (
    transform_support_tickets
)
from backend.etl.transform.transform_transactions import (
    transform_transactions
)
from backend.etl.transform.transform_user_roles import transform_user_roles


class Transformer:
    """
    Central transformation engine for FinIntel AI.

    Applies generic cleaning rules followed by
    dataset-specific transformations.
    """

    def __init__(self, dataframe, dataset_name):
        self.df = dataframe
        self.dataset_name = dataset_name

    def transform(self):
        print(
            f"Applying transformations : {self.dataset_name}"
        )

        # ========================================================
        # GENERIC TRANSFORMATIONS
        # ========================================================

        transformed_df = apply_generic_rules(self.df)

        # ========================================================
        # DATASET-SPECIFIC TRANSFORMATIONS
        # ========================================================

        transformation_map = {
            "customers": transform_customers,
            "accounts": transform_accounts,
            "transactions": transform_transactions,
            "loan_applications": transform_loans,
            "credit_card_fraud": transform_credit_card_fraud,
            "branch_performance": transform_branch_performance,
            "branches": transform_branches,
            "banking_products": transform_banking_products,
            "employees": transform_employees,
            "marketing_campaigns": transform_marketing_campaigns,
            "support_tickets": transform_support_tickets,
            "user_roles": transform_user_roles,
            "prediction_history": transform_prediction_history,

            # Give Me Some Credit
            "give_me_some_credit_credit_score_train":
                transform_credit_score,

            "give_me_some_credit_credit_score_test":
                transform_credit_score,

            # German Credit
            "german_credit_german":
                transform_german_credit,
        }

        transformation_function = transformation_map.get(
            self.dataset_name
        )

        if transformation_function:
            transformed_df = transformation_function(
                transformed_df
            )
        else:
            print(
                f"No dataset-specific transformation found "
                f"for: {self.dataset_name}"
            )

        return transformed_df