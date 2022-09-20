import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="auth",
    version="0.0.1",
    description="SFTP Server",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="author",
    package_dir={"": "lib"},
    packages=setuptools.find_packages(where="auth"),
    install_requires=[
        "aws-cdk-lib==2.41.0",
        "constructs>=10.0.0,<11.0.0"
    ],
)
