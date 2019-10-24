FROM catenae/link:2.0.0
ADD pypow.py /opt/catenae
ENTRYPOINT ["python", "pypow.py"]
