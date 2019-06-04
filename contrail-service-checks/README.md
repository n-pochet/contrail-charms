# Overview

The goal of this charm is to provide NRPE checks for Contrail. It will pull the alarms from Contrail analytics. If an alarm is found, a CRITICAL response is sent to NRPE. If no alarm is found, an OK response is sent to NRPE.

# Usage

```bash
# Assuming that a working Contrail + OpenStack environment is already deployed with Nagios and NRPE
charm build ./contrail-service-checks
juju deploy /tmp/charm-builds/contrail-service-checks
juju config contrail-service-checks contrail_analytics_vip=VIP
juju add-relation nrpe contrail-service-checks
juju add-relation keystone contrail-service-checks
```


## Scale out Usage

There is no use to scale this charm.

## Known Limitations and Issues

* No scale out
* Not tested against a cloud with HTTPS for Keystone
* Basic checks of the Contrail alarms:
  * If there's any alarm -> CRITICAL
  * If there's no alarm -> OK
  * In any case, print the result of the query

