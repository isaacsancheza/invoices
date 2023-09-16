import aws_cdk as cdk
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_ses as ses
from aws_cdk import aws_ses_actions as actions
from aws_cdk import aws_stepfunctions as sfn
from aws_cdk import aws_stepfunctions_tasks as tasks
from aws_cdk import aws_lambda as lambda_
from constructs import Construct


class LambdaFunction(Construct):
    def __init__(self, scope: Construct, construct_id: str, source_code_path: str, timeout: int = 60) -> None:
        super().__init__(scope, construct_id)

        function_kwargs = {
            'code': lambda_.Code.from_asset(source_code_path, bundling=cdk.BundlingOptions(
                image=lambda_.Runtime.PYTHON_3_10.bundling_image, 
                command=['bash', '-c', 'pip install -r requirements.txt -t /asset-output && cp -au . /asset-output',
            ])),
            'handler': 'lambda.handler',
            'timeout': cdk.Duration.seconds(timeout),
            'tracing': lambda_.Tracing.ACTIVE,
            'runtime': lambda_.Runtime.PYTHON_3_10,
        }
        self.function: lambda_.Function = lambda_.Function(self, 'Function', **function_kwargs)


class Stack(cdk.Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        bucket: s3.Bucket = s3.Bucket(self, 'Bucket', bucket_name='abax', auto_delete_objects=True, removal_policy=cdk.RemovalPolicy.DESTROY)
        rule_set: ses.ReceiptRuleSet = ses.ReceiptRuleSet.from_receipt_rule_set_name(self, 'RuleSet', 'default-receipt-rule-set')
        
        rule_set.add_rule('Invoices', receipt_rule_name='invoices', recipients=['facturas@correo.elrincondelsanchez.com',], actions=[actions.S3(bucket=bucket, object_key_prefix='emails')])

        choose_parser: LambdaFunction = LambdaFunction(self, 'ChooseParser', '/workspace/functions/shared/choose-parser/src')
        
        state_machine: sfn.StateMachine = sfn.StateMachine(self, '')
        bucket.add_event_notification(s3.EventType.OBJECT_CREATED_PUT, )


app = cdk.App()

Stack(app, 'RootStack', stack_name='abax')

app.synth()
