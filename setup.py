from setuptools import setup, find_packages

setup(
    name='VecTank',
    use_scm_version=True,
    setup_requires=['setuptools_scm'],
    description='軽量で高速なインメモリベクトル検索およびタンク操作ライブラリ',
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author='satorunnlg',
    author_email='satorunnlg@gmail.com',
    url="https://github.com/satorunnlg/VecTank.git",
    packages=find_packages(),
    install_requires=[
        'numpy',
    ],
    entry_points={
        'console_scripts': [
            'vectank-run=vectank.server:main',
        ],
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.7',
)
