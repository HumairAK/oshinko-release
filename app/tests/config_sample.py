config = {
  "CELERY_BROKER_URL": "amqp://localhost//",
  "CELERY_RESULT_BACKEND": "db+postgresql://userQJC:I5g0wmW3qSub8N6f@localhost:5432/sampledb",
  "CELERY_TRACK_STARTED": "True",
  "DEFAULT": {
    "PORT": "8085",
    "IP": "localhost"
  },
  "GH_USER_INFO": {
    "GH_USER": "commit-tester",
    "GH_EMAIL": "committer829@gmail.com",
    "GH_AUTH_TOKEN": "a3e342ed5f1e32cac9d632a44342a465sed11e35c"
  },
  "CELERY_ONCE": {
    "BACKEND": "celery_once.backends.Redis",
    "SETTINGS": {
      "URL": "redis://localhost:6379/0?password=bV3aNcKuakPqxJbd",
      "DEFAULT_TIMEOUT": "3600"
    }
  },
  "UPSTREAM_REPOS": {
    "OPENSHIFT_SPARK": "radanalyticsio/openshift-spark",
    "OSHINKO_CLI": "radanalyticsio/oshinko-cli",
    "OSHINKO_S2I": "radanalyticsio/oshinko-s2i",
    "OSHINKO_WEBUI": "radanalyticsio/oshinko-webui",
    "OC_PROXY": "radanalyticsio/oshinko-cli"
  },
  "DOCKERHUB_REPOS": {
    "OPENSHIFT_SPARK": {
      "REPO" : "radanalyticsio/openshift-spark",
      "TOKEN": "e59fb0d4b9a92"
    },
    "OSHINKO_CLI": {
      "REPO" : "radanalyticsio/oshinko-rest",
      "TOKEN": "1dc107df-2fa2"
    },
    "OSHINKO_S2I_SCALA": {
      "REPO" : "radanalyticsio/radanalytics-scala-spark",
      "TOKEN": "c1f2efa9-5b2a"
    },
    "OSHINKO_S2I_JAVA": {
      "REPO" : "radanalyticsio/radanalytics-java-spark",
      "TOKEN": "617908dc-8b0d"
    },
    "OSHINKO_S2I_PYSPARK": {
      "REPO" : "radanalyticsio/radanalytics-pyspark",
      "TOKEN": "5815a5b1-7842"
    },
    "OSHINKO_WEBUI":  {
      "REPO" : "radanalyticsio/oshinko-webui",
      "TOKEN": "29c91045-f03f"
    },
    "OC_PROXY": {
      "REPO" : "radanalyticsio/oc-proxy",
      "TOKEN": "9c6dcfe1-eaad"
    }
  }
}