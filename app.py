#!/usr/bin/env python3
import os

from aws_iot.aws_iot_stack import AwsIotStack

#!/usr/bin/env python3
import aws_cdk as cdk
from aws_cdk import (
    aws_lambda as _lambda,
    aws_iot as iot,
    aws_iam as iam,
    aws_dynamodb as dynamodb,
    RemovalPolicy
)
from constructs import Construct

class TemperatureLambdaStack(cdk.Stack):

    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Crear la tabla DynamoDB
        table = dynamodb.Table(
            self, "TemperatureDataTable",
            partition_key=dynamodb.Attribute(
                name="deviceId",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.NUMBER
            ),
            removal_policy=RemovalPolicy.DESTROY,  # Solo para desarrollo
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST
        )

        # Crear la función Lambda
        lambda_fn = _lambda.Function(
            self, "TemperatureLambdaHandler",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="temperature_handler.lambda_handler",  # Ubicación del código Lambda
            code=_lambda.Code.from_asset("lambda"),  # Ruta a la carpeta lambda/
            environment={
                "DYNAMODB_TABLE_NAME": table.table_name
            }
        )

        # Otorgar permisos a Lambda para escribir en DynamoDB
        table.grant_write_data(lambda_fn)

        # Crear el rol IoT para invocar Lambda
        iot_role = iam.Role(
            self, "IoTRole",
            assumed_by=iam.ServicePrincipal("iot.amazonaws.com")
        )

        # Otorgar permisos al rol IoT para invocar Lambda
        iot_role.add_to_policy(
            iam.PolicyStatement(
                actions=["lambda:InvokeFunction"],
                resources=[lambda_fn.function_arn]
            )
        )

        # Crear la regla IoT para invocar la Lambda en el tema 'temperature'
        iot_topic_rule = iot.CfnTopicRule(
            self, "TemperatureRule",
            topic_rule_payload=iot.CfnTopicRule.TopicRulePayloadProperty(
                sql="SELECT * FROM 'temperature'",  # SQL para escuchar en el tema
                actions=[
                    iot.CfnTopicRule.ActionProperty(
                        lambda_=iot.CfnTopicRule.LambdaActionProperty(
                            function_arn=lambda_fn.function_arn
                        )
                    )
                ],
                rule_disabled=False
            )
        )

        # Permitir a Lambda ser invocada por IoT Core
        lambda_fn.add_permission(
            "AllowIoTInvoke",
            principal=iam.ServicePrincipal("iot.amazonaws.com"),
            source_arn=iot_topic_rule.attr_arn
        )

app = cdk.App()
TemperatureLambdaStack(app, "TemperatureLambdaStack")
app.synth()

