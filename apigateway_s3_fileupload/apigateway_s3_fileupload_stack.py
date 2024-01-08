from aws_cdk import (
    Stack,
    aws_apigateway, 
    aws_iam, 
    aws_s3, 
    RemovalPolicy, 
    aws_logs
)

from constructs import Construct

class ApigatewayS3FileuploadStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.create_apigateway_role()
        self.create_s3_bucket()
        self.create_api_gateway()
        
    def create_apigateway_role(self):
        self.apigateway_role = aws_iam.Role(
            scope=self, 
            id="apigatewayS3AccessRole", 
            role_name="apigatewayS3AccessRole", 
            assumed_by=aws_iam.ServicePrincipal("apigateway.amazonaws.com")
        )
        
        self.apigateway_role.apply_removal_policy(RemovalPolicy.DESTROY)
        self.apigateway_role.add_managed_policy(
            aws_iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AmazonAPIGatewayPushToCloudWatchLogs")
        )

    def create_s3_bucket(self): 
        self.bucket = aws_s3.Bucket(
            scope=self, 
            id="apigatewayS3DataBucket", 
            bucket_name="apigateway-s3-demo-bucket"
        )
        self.bucket.apply_removal_policy(RemovalPolicy.DESTROY)
        self.bucket.grant_read_write(self.apigateway_role)


    def create_api_gateway(self):
        access_log = aws_logs.LogGroup(
            scope=self, 
            id="apigatewayS3DemoAccessLog",
            log_group_name="apigatewayS3DemoAccessLog", 
            retention=aws_logs.RetentionDays.ONE_WEEK
        )
        access_log.apply_removal_policy(RemovalPolicy.DESTROY)
        
        inegration_responses = [
            aws_apigateway.IntegrationResponse(
                status_code="200", 
                response_parameters={
                    'method.response.header.Timestamp':'integration.response.header.Date',
                    'method.response.header.Content-Length':'integration.response.header.Content-Length',
                    'method.response.header.Content-Type':'integration.response.header.Content-Type',
                    'method.response.header.Access-Control-Allow-Origin': "'*'",
                }
            ), 
            aws_apigateway.IntegrationResponse(
                status_code="400", 
                response_parameters={
                    'method.response.header.Access-Control-Allow-Origin': "'*'",
                }, 
                selection_pattern="4\d{2}"
            ), 
            aws_apigateway.IntegrationResponse(
                status_code="500", 
                response_parameters={
                    'method.response.header.Access-Control-Allow-Origin': "'*'",
                }, 
                selection_pattern="5\d{2}"
            ), 
            
        ]
        
        method_responses=[
            aws_apigateway.MethodResponse(
                status_code="200", 
                response_parameters={
                    'method.response.header.Timestamp': True,
                    'method.response.header.Content-Length': True,
                    'method.response.header.Content-Type': True,
                    'method.response.header.Access-Control-Allow-Methods': True,
                    'method.response.header.Access-Control-Allow-Origin': True,
                }
            ), 
            aws_apigateway.MethodResponse(
                status_code="400", 
                response_parameters={
                    'method.response.header.Access-Control-Allow-Methods': True,
                    'method.response.header.Access-Control-Allow-Origin': True,
                }
            ), 
            aws_apigateway.MethodResponse(
                status_code="500", 
                response_parameters={
                    'method.response.header.Access-Control-Allow-Methods': True,
                    'method.response.header.Access-Control-Allow-Origin': True,
                }
            ), 
        ]
        
        self.apigateway = aws_apigateway.RestApi(
            scope=self, 
            id="apigatewayS3RestAPI", 
            rest_api_name="apigatewayS3CDKRestAPI", 
            cloud_watch_role=True,
            endpoint_types=[aws_apigateway.EndpointType.REGIONAL],
            deploy_options=aws_apigateway.StageOptions(
                access_log_destination=aws_apigateway.LogGroupLogDestination(access_log),
                logging_level=aws_apigateway.MethodLoggingLevel.INFO, 
                data_trace_enabled=True
            ), 
            binary_media_types=["image/jpeg"]
        )
        self.apigateway.apply_removal_policy(RemovalPolicy.DESTROY)
        
        self.apigateway.root.add_method(
            "GET",
            aws_apigateway.AwsIntegration(
                service="s3", 
                integration_http_method="GET", 
                path=f"{self.bucket.bucket_name}", 
                region=self.region, 
                options=aws_apigateway.IntegrationOptions(
                    credentials_role=self.apigateway_role, 
                    integration_responses=inegration_responses, 
                )                
            ), 
            method_responses=method_responses
        )
        
        self.apigateway_object = self.apigateway.root.add_resource(
            "{object}"
        )

        self.apigateway_object.add_method(
            "GET",
            aws_apigateway.AwsIntegration(
                service="s3", 
                integration_http_method="GET", 
                path=f"{self.bucket.bucket_name}/{{object}}", 
                region=self.region, 
                options=aws_apigateway.IntegrationOptions(
                    credentials_role=self.apigateway_role, 
                    request_parameters={
                        "integration.request.path.object": "method.request.path.object"
                    }, 
                    integration_responses=inegration_responses, 
                )                
            ),
            method_responses=method_responses, 
            request_parameters={
                "method.request.path.object": True, 
                "method.request.header.Accept": False
            } 
        )
        
        self.apigateway_object.add_method(
            "PUT",
            aws_apigateway.AwsIntegration(
                service="s3", 
                integration_http_method="PUT", 
                path=f"{self.bucket.bucket_name}/{{object}}", 
                region=self.region, 
                options=aws_apigateway.IntegrationOptions(
                    credentials_role=self.apigateway_role, 
                    request_parameters={
                        "integration.request.path.object": "method.request.path.object"
                    }, 
                    integration_responses=inegration_responses
                )                
            ),
            method_responses=method_responses, 
            request_parameters={
                "method.request.path.object": True, 
                "method.request.header.Content-Type": False
            }
        )