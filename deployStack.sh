export CURRENT_TIMESTAMP=$(date +%s)
export CURRENT_REGION=`aws configure get region`
export ACCOUNT_ID=`aws sts get-caller-identity | jq -r .Account`
export BUCKET_NAME="scan-file-$ACCOUNT_ID-$CURRENT_TIMESTAMP"

echo $AWS_REGION

if [ -z "$AWS_REGION" ]; then
        export AWS_REGION=$CURRENT_REGION
fi

echo $AWS_REGION

if [ "$AWS_REGION" = "us-east-1" ]
then
    echo $AWS_REGION
  aws s3api create-bucket --bucket $BUCKET_NAME
else
  aws s3api create-bucket --bucket $BUCKET_NAME --region $AWS_REGION --create-bucket-configuration LocationConstraint=$AWS_REGION
fi


cd ./virusscan/constructs/workflow/lib/src/

zip -r -j scan-file.zip scanfile/

aws s3 cp scan-file.zip s3://$BUCKET_NAME

cd ../../../../../

aws cloudformation create-stack --stack-name clamav-codebuild --template-body file://anti-virus-code-build.yaml --parameters ParameterKey=UploadBucketName,ParameterValue=$BUCKET_NAME --capabilities CAPABILITY_NAMED_IAM

aws cloudformation wait stack-create-complete --stack-name clamav-codebuild


export CODE_BUILD_PROJECT=`aws cloudformation describe-stacks | jq -r --arg STACK_NAME "clamav-codebuild" '.Stacks[] | select(.StackName=="clamav-codebuild") | .Outputs[] | select(.OutputKey=="codeBuildResource") | .OutputValue'`

aws codebuild start-build --project-name $CODE_BUILD_PROJECT --no-cli-pager

id=$(aws codebuild list-builds-for-project --project-name $CODE_BUILD_PROJECT | jq -r '.ids[0]')

function getstatus {
    aws codebuild batch-get-builds --ids "$id" | jq -r '.builds[].phases[] | select (.phaseType=="COMPLETED") | .phaseType'
}

while [[ $(getstatus) != "COMPLETED" ]]
do
 sleep 15
 echo "Still building"
done

aws cloudformation create-stack --stack-name clamav-scan --template-body file://anti-virus-scan-template.yaml --parameters ParameterKey=CodeBuildStack,ParameterValue=clamav-codebuild ParameterKey=UserName,ParameterValue=$1 ParameterKey=Password,ParameterValue=$2 --capabilities CAPABILITY_NAMED_IAM

aws cloudformation wait stack-create-complete --stack-name clamav-scan

export SFTP_ENDPOINT=`aws cloudformation describe-stacks | jq -r --arg STACK_NAME "clamav-scan" '.Stacks[] | select(.StackName=="clamav-scan") | .Outputs[] | select(.OutputKey=="SFTPEndpoint") | .OutputValue'`

echo "SFTPEndpoint"
echo $SFTP_ENDPOINT