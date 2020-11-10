FROM catenae/link-stopover
ADD pypow.py /opt/catenae
ENTRYPOINT ["python", "pypow.py"]