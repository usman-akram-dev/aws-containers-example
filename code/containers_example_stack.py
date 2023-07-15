from constructs import Construct

from os import path
from aws_cdk import (
    Stack,
    CfnOutput,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_elasticloadbalancingv2 as elbv2,
    Duration,
    RemovalPolicy,
    Stack,
    aws_ec2 as ec2,
    aws_rds as rds,
    aws_secretsmanager as secretsmanager,
    aws_ecr_assets as ecr_assets,
    aws_ecs as ecs,
    aws_ecs_patterns as patterns,
    aws_elasticloadbalancingv2 as elb2,
    aws_secretsmanager as secretsmanager,
    aws_sns as sns,
    aws_sns_subscriptions as subscriptions,
    aws_cloudwatch as cloudwatch,
    aws_cloudwatch_actions as cw_actions,


)
from aws_cdk.aws_iam import Effect, ManagedPolicy, Policy, PolicyStatement

from constructs import Construct

class ContainersExampleStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # create a vpc
        self.vpc = ec2.Vpc(self, 'ContainerExampleVPC')

        #create tour ecs cluster
        self.cluster = ecs.Cluster(self, 'ContainerExampleCluster',
            vpc=self.vpc,
            cluster_name='ContainerExampleCluster',
            container_insights=True,
            

        )

        # create security group
        self.db_service_sg = ec2.SecurityGroup(
            self, 
            "DbFargateServiceSg",
            allow_all_outbound=True,
            description="Security group for DB service",
            vpc=self.vpc
        )

        # Security group for Api service
        self.api_service_sg = ec2.SecurityGroup(
            self, 
            "ContainerFargateServiceSg",
            allow_all_outbound=True,
            description="Security group for Api service",
            vpc=self.vpc
        )

        # create ALB to accept traffic for your application
        self.alb = elbv2.ApplicationLoadBalancer(
            self,
            'ContainerServiceAlb',
            vpc=self.vpc,
            internet_facing=True,
        )
        # CfnOutput(self, 
        #     'LinkToAlb', 
        #     value=self.alb.load_balancer_dns_name
        # )


        # Allow Api Service SG to connect to DB Service on port 5432
        self.db_service_sg.add_ingress_rule(
            self.api_service_sg,
            ec2.Port.tcp(5432),
            'Allow DB connection from ConsainerService'
        )

        CfnOutput(self, 
            'LinkToEcsCluster', 
            value=f'https://{self.region}.console.aws.amazon.com/ecs/home?region={self.region}#/clusters/{self.cluster.cluster_name}/fargateServices'
        )


        # create database
        db_cluster: rds.DatabaseCluster = rds.DatabaseCluster(self,
            'DbAuroraCluster',
            engine=rds.DatabaseClusterEngine.aurora_postgres(
                version=rds.AuroraPostgresEngineVersion.VER_15_2
            ),
            instance_props=rds.InstanceProps(
                instance_type=ec2.InstanceType.of(
                    ec2.InstanceClass.BURSTABLE4_GRAVITON, 
                    ec2.InstanceSize.MEDIUM
                ),
                vpc=self.vpc,
                vpc_subnets= {
                    'subnet_type': ec2.SubnetType.PRIVATE_WITH_EGRESS
                },
                security_groups=[self.db_service_sg],

                # Disallow minor version auto upgrade
                auto_minor_version_upgrade=False,

                # Block people from accidentally delete the database. 
                # I do not enable this as you may unintentionally leave the db in your test account
                # and get charged extra. 
                # deletion_protection=True,
            ),
            default_database_name='sample_db',

            # not recommended for production
            storage_encrypted= False, 

            # not recommended for production
            removal_policy=RemovalPolicy.DESTROY,

            
            # If you don't specify preferred maintenance window, RDS will speculate the time based on your region
            # https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_UpgradeDBInstance.Maintenance.html#Concepts.DBMaintenance
            preferred_maintenance_window='Sun:19:00-Sun:22:00',

            # Snapshot setting. Note that automated backup snapshot is deleted with the instance is deleted. (or REPLACE when updated in CloudFormation)
            # Only manual snapshots are retained.
            backup=rds.BackupProps(
                retention=Duration.days(1),
                preferred_window='22:00-23:00',
            ),

        )

        self.db_secret_store: secretsmanager.ISecret = db_cluster.secret        

        # deploy code as container into the ECR registry. This could be a separate repo where developers add the stuff or
        # your CI/CD pipeline that build the image
        self.api_image: ecr_assets.DockerImageAsset = ecr_assets.DockerImageAsset(
            self,
            'ApiImage',
            directory=path.join('.', 'services' ),
            file='Dockerfile'
        )


        # deploy container on the fargate
        alb_fargate: patterns.ApplicationLoadBalancedFargateService = patterns.ApplicationLoadBalancedFargateService(
            self, 
            'ApiService',
            cluster=self.cluster,
            # Service
            service_name='ApiService',
            cpu= 256,
            memory_limit_mib=512,
            task_image_options= patterns.ApplicationLoadBalancedTaskImageOptions(
                image=ecs.ContainerImage.from_docker_image_asset(self.api_image),
                container_port=3000,
                enable_logging=True,
                environment= {
                    'KEY': 'VALUE',
                },
                secrets={
                    'SQL_HOST': ecs.Secret.from_secrets_manager(self.db_secret_store, 'host'),
                    'SQL_PORT': ecs.Secret.from_secrets_manager(self.db_secret_store, 'port'),
                    'DATABASE': ecs.Secret.from_secrets_manager(self.db_secret_store, 'engine'),
                    'USERNAME': ecs.Secret.from_secrets_manager(self.db_secret_store, 'username'),
                    'PASSWORD': ecs.Secret.from_secrets_manager(self.db_secret_store, 'password'),
                }
            ),
            # Load balancer
            load_balancer=self.alb,
            public_load_balancer=True,
            listener_port=80,
            security_groups=[
                self.api_service_sg,
            ],
            runtime_platform=ecs.RuntimePlatform( operating_system_family=ecs.OperatingSystemFamily.LINUX,
                    cpu_architecture=ecs.CpuArchitecture.ARM64),
        )
        
        # default is 5 mins
        alb_fargate.target_group.set_attribute(key="deregistration_delay.timeout_seconds", value="10")
        



        # Check "Author's Insights" section for other options.
        alb_fargate.target_group.configure_health_check(
            path='/healthcheck'
        )

        autoscale = alb_fargate.service.auto_scale_task_count(
            min_capacity=1,
            max_capacity=5,
        )

        autoscale.scale_on_cpu_utilization(
            'CpuAutoScaling',
            target_utilization_percent=30,
            scale_in_cooldown=Duration.seconds(30),
            scale_out_cooldown=Duration.seconds(30),
        )

        alb_fargate.task_definition.task_role.add_to_policy(
            PolicyStatement(
                effect=Effect.ALLOW,
                actions=['cloudwatch:PutMetricData'],
                resources=['*'],
            )
        )
        
        ## upto reader to enhance the code to record the metrics and generate alerts


                