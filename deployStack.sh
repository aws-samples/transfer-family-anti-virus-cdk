aws s3api create-bucket --bucket scan-file 

cd virusscan/constructs/workflow/lib/src/

zip -r -j scan-file.zip scanfile/

aws s3 cp scan-file.zip s3://scan-file

cd 

cd transfer-family-anti-virus-cdk 

aws cloudformation create-stack --stack-name clamav-codebuild --template-body file://anti-virus-code-build.yaml --parameters ParameterKey=UploadBucketName,ParameterValue=scan-file --capabilities CAPABILITY_NAMED_IAM

aws cloudformation wait stack-create-complete --stack-name clamav-codebuild


export CODE_BUILD_PROJECT=`aws cloudformation describe-stacks | jq -r --arg STACK_NAME "clamav-codebuild" '.Stacks[] | select(.StackName=="clamav-codebuild") | .Outputs[] | select(.OutputKey=="codeBuildResource") | .OutputValue'`

aws codebuild start-build --project-name $CODE_BUILD_PROJECT

id=$(aws codebuild list-builds-for-project --project-name $CODE_BUILD_PROJECT | jq -r '.ids[0]')

function getstatus {
    aws codebuild batch-get-builds --ids "$id" | jq -r '.builds[].phases[] | select (.phaseType=="COMPLETED") | .phaseType'
}

while [[ $(getstatus) != "COMPLETED" ]]
do
 sleep 15
 echo "Still building"
done

aws cloudformation create-stack --stack-name clamav-scan --template-body file://anti-virus-scan-template.yaml --parameters ParameterKey=CodeBuildStack,ParameterValue=clamav-codebuild --capabilities CAPABILITY_NAMED_IAM

aws cloudformation wait stack-create-complete --stack-name clamav-scan

export SFTP_ENDPOINT=`aws cloudformation describe-stacks | jq -r --arg STACK_NAME "clamav-scan" '.Stacks[] | select(.StackName=="clamav-scan") | .Outputs[] | select(.OutputKey=="SFTPEndpoint") | .OutputValue'`
export USER_NAME=`aws cloudformation describe-stacks | jq -r --arg STACK_NAME "clamav-scan" '.Stacks[] | select(.StackName=="clamav-scan") | .Outputs[] | select(.OutputKey=="Username") | .OutputValue'`
export PASSWORD=`aws cloudformation describe-stacks | jq -r --arg STACK_NAME "clamav-scan" '.Stacks[] | select(.StackName=="clamav-scan") | .Outputs[] | select(.OutputKey=="Password") | .OutputValue'`

echo "SFTPEndpoint"
echo $SFTP_ENDPOINT
echo "Username"
echo $USER_NAME
echo "Password is"
echo $PASSWORD