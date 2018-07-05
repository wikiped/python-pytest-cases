from pytest_cases import test_steps, cases_data, CaseDataGetter, THIS_MODULE, MultipleStepsCaseData


def case_simple() -> MultipleStepsCaseData:
    ins = dict(a=1, b=2)

    outs_for_a = 2, 3
    outs_for_b = 5, 4
    outs = dict(step_check_a=outs_for_a, step_check_b=outs_for_b)

    return ins, outs, None


def case_simple2() -> MultipleStepsCaseData:
    ins = dict(a=-1, b=2)

    outs_for_a = 2, 3
    outs_for_b = 5, 4
    outs = dict(step_check_a=outs_for_a, step_check_b=outs_for_b)

    return ins, outs, None


def step_check_a(ins, expected_o, expected_e):
    """ Step a of the test """

    # Use the three items as usual
    print(ins)


def step_check_b(ins, expected_o, expected_e):
    """ Step b of the test """

    # Use the three items as usual
    print(ins)


# equivalent to @pytest.mark.parametrize('test_step', (step_check_a, step_check_b), ids=lambda x: x.__name__)
@test_steps(step_check_a, step_check_b)
@cases_data(module=THIS_MODULE)
def test_suite(test_step, case_data: CaseDataGetter):

    # Get the data for this step
    ins, expected_o, expected_e = case_data.get_for(test_step.__name__)

    # Execute the step
    test_step(ins, expected_o, expected_e)
