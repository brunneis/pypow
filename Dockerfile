FROM catenae/link:develop
ADD pypow.py /opt/catenae
ENTRYPOINT ["python", "pypow.py"]
