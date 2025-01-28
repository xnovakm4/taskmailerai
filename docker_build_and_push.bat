@echo off
REM Set variables
set REPOSITORY=xnovakm4/taskmailerai
set TAG=latest

REM Build full image name
set IMAGE_NAME=%REPOSITORY%:%TAG%

echo Building Docker image: %IMAGE_NAME%
docker build -t %IMAGE_NAME% .
IF ERRORLEVEL 1 (
    echo Error: Docker image build failed!
    exit /b 1
)

echo Docker image built successfully!

echo Pushing Docker image to repository: %REPOSITORY%
docker push %IMAGE_NAME%
IF ERRORLEVEL 1 (
    echo Error: Docker push failed!
    exit /b 1
)

echo Docker image pushed successfully!
exit /b 0