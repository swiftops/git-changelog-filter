from setuptools import setup, find_packages

setup(
    name='Change Log Filter Service',
    version='1.0.0',
    description='This service is used to filter request and response of Change Log',
    author='Sakina Shaikh',
    author_email='sakina.shaikh@digite.com',
    url='',#<URl>
    keywords=["Swagger", "Change Log Filter Service"],
    install_requires=open('requirements.txt').read(),
    packages=find_packages(),
    include_package_data=True,
    license='',
    long_description=open('README.md').read()
	#test_suite='nose.collector',
    #tests_require=['nose']
)