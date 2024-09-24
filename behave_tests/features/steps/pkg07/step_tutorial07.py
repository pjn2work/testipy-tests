from behave import given, when, then
from behave.runner import Context


@given('we2 have behave installed')
def step_impl7(context: Context):
    print(">>>>> given 7", context)
