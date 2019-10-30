from charmhelpers.core.hookenv import (
    action_get,
    action_fail,
    action_set,
    status_set,
    log,
)
from charms.reactive import (
    clear_flag,
    set_flag,
    when,
    when_not,
)

import charms.sshproxy
import sys, traceback

class TestMetricsException(Exception):
    pass

@when_not('testmetrics.installed')
def install_testmetrics():
    set_flag('testmetrics.installed')

@when('actions.setup-testmetrics')
def setup_testmetrics():
    err = ''
    try:
        #param1 = action_get('param1')

        cfg = charms.sshproxy.get_config()
        host = charms.sshproxy.get_host_ip()
        user = cfg['ssh-username']
        charms.sshproxy.sftp('scripts/get-metric.sh', '/home/ubuntu/get-metric.sh', host, user)

        cmd = "chmod +x /home/ubuntu/get-metric.sh && echo 'OK'"
        log("setup-testmetrics: command to execute: " + cmd)
        result, err = charms.sshproxy._run(cmd)
        log("setup-testmetrics: DONE")
    except:
        log("Error. Command Failed.")
        action_fail('command failed:' + err)
        exc_type, exc_value, exc_traceback = sys.exc_info()
        err = traceback.format_exception(exc_type, exc_value, exc_traceback)
        log(str(err))
    else:
        action_set({'output': result})
    finally:
        clear_flag('actions.setup-testmetrics')

@when('actions.add-machines')
def add_machines():
    err = ''
    try:
        machines = []
        machines.append(action_get('machine1'))
        machines.append(action_get('machine2'))
        machines.append(action_get('machine3'))
        machines.append(action_get('machine4'))
        machines.append(action_get('machine5'))
        machines.append(action_get('machine6'))
        machines.append(action_get('machine7'))
        machines.append(action_get('machine8'))
        machines.append(action_get('machine9'))
        machines.append(action_get('machine10'))

        cfg = charms.sshproxy.get_config()
        host = charms.sshproxy.get_host_ip()
        user = cfg['ssh-username']
        charms.sshproxy.sftp('scripts/add-machine.sh', '/home/ubuntu/add-machine.sh', host, user)

        cmd = "chmod +x /home/ubuntu/add-machine.sh"
        log("add-machines: command to execute: " + cmd)
        result, err = charms.sshproxy._run(cmd)

        number_of_machines = 0
        for m in machines:
            if not m:
                continue
            cmd = "/home/ubuntu/add-machine.sh {} > /dev/null && echo 'OK'".format(m)
            log("add-machines: command to execute: " + cmd)
            result, err = charms.sshproxy._run(cmd)
            log("add-machines: added {}".format(m))
            number_of_machines += 1
        log("add-machines: Checking whether all machines are ready")
        timeout = 0
        while timeout <= 600:
            try:
                started = 0
                cmd = "/snap/bin/juju machines --format yaml"
                log("add-machines: getting machines: " + cmd)
                result, err = charms.sshproxy._run(cmd)
                juju_machines = yaml.safe_load(result)
                for k,v in juju_machines['machines'].items():
                    if v.get('juju-status').get('current') == "started":
                        started += 1
                if started >= number_of_machines:
                    log("add-machines: {}/{} machines are ready".format(started,number_of_machines))
                    break
                log("add-machines: {}/{} machines are ready".format(started,number_of_machines))
            except:
                log("Error. Command Failed." + str(err))
            time.sleep(20)
            timeout += 20
        else:
            log("add-machines: Machines are not ready after {} seconds.".format(timeout))
            raise TidJujuK8sException("Timeout when adding machines")
        log("add-machines: DONE")
    except TidJujuK8sException as toexception:
        log("add-machines: TidJujuK8sException:" + str(toexception))
        action_fail('Timeout reached for adding machines:' + str(toexception))
    except:
        log("Error. Command Failed.")
        action_fail('command failed:' + err)
        exc_type, exc_value, exc_traceback = sys.exc_info()
        err = traceback.format_exception(exc_type, exc_value, exc_traceback)
        log(str(err))
    else:
        action_set({'output': result})
    finally:
        clear_flag('actions.add-machines')

@when('actions.deploy-bundle')
def deploy_bundle():
    err = ''
    try:
        cmd = "/snap/bin/juju machines --format yaml"
        log("deploy-bundle: getting machines: " + cmd)
        result, err = charms.sshproxy._run(cmd)
        juju_machines = yaml.safe_load(result)
        n_machines = len(juju_machines['machines'])

        bundle = action_get('bundle')
        bundle_dict = {}
        if bundle:
            try:
                bundle_dict = yaml.safe_load(bundle)
            except yaml.YAMLError as exc:
                raise TidJujuK8sException("Error loading the provided bundle " + bundle + ": " + str(exc))
        else:
            with open("scripts/bundle-empty.yaml", 'r') as stream:
                try:
                    bundle_dict = yaml.safe_load(stream)
                except yaml.YAMLError as exc:
                    raise TidJujuK8sException("Error loading the default bundle bundle-empty.yaml: " + str(exc))
            if n_machines < 4:
                raise TidJujuK8sException("Not possible to deploy a bundle when number of machines is lower than 4")
            else:
                n_etcd = 3
                n_masters = 2
                n_workers = n_machines - 1
                bundle_dict["machines"]={}
                #bundle_dict["machines"].extend(map(str,range(n_machines)))
                for i in range(n_machines):
                    bundle_dict["machines"][str(i)] = {}
                bundle_dict["services"]["easyrsa"]["to"]=[]
                bundle_dict["services"]["easyrsa"]["to"].append("0")
                bundle_dict["services"]["kubeapi-load-balancer"]["to"]=[]
                bundle_dict["services"]["kubeapi-load-balancer"]["to"].append("0")
                bundle_dict["services"]["etcd"]["to"]=[]
                bundle_dict["services"]["etcd"]["to"].extend(map(str,range(0,n_etcd+1)))
                bundle_dict["services"]["kubernetes-master"]["to"]=[]
                bundle_dict["services"]["kubernetes-master"]["to"].extend(map(str,range(0,n_masters+1)))
                bundle_dict["services"]["kubernetes-worker"]["to"]=[]
                bundle_dict["services"]["kubernetes-worker"]["to"].extend(map(str,range(1,n_workers+1)))

        with open("scripts/bundle.yaml", 'w') as stream:
            try:
                yaml.safe_dump(bundle_dict, stream)
            except yaml.YAMLError as exc:
                raise TidJujuK8sException("Error while dumping bundle_dict to bundle.yaml: " + str(exc))

        cfg = charms.sshproxy.get_config()
        host = charms.sshproxy.get_host_ip()
        user = cfg['ssh-username']
        charms.sshproxy.sftp('scripts/bundle.yaml', '/home/ubuntu/bundle.yaml', host, user)

        existing_machines = []
        map_machines = ""
        bundle_machine = 0
        for k in juju_machines['machines']:
            map_machines = "{}{}={}".format(map_machines, bundle_machine, k)
            bundle_machine += 1
            if bundle_machine < n_machines:
                map_machines += ","
        log("deploy-bundle: map_machines: " + map_machines)

        cmd = "/snap/bin/juju deploy ./bundle.yaml --map-machines=existing,{}".format(map_machines)
        log("deploy-bundle: command to execute: " + cmd)
        result, err = charms.sshproxy._run(cmd)
        log("deploy-bundle: Checking whether all applications in the bundle are active")
        timeout = 0
        while timeout <= 1800:
            try:
                cmd = "/snap/bin/juju status --format yaml"
                log("deploy-bundle: getting status: " + cmd)
                result, err = charms.sshproxy._run(cmd)
                juju_status = yaml.safe_load(result)
                for k,v in juju_status['applications'].items():
                    if v.get('application-status').get('current') != 'active':
                        log('deploy-bundle: Application {} not active'.format(k))
                        break
                else:
                    log('deploy-bundle: All applications are active')
                    break
            except:
                log("Error. Command Failed." + str(err))
            time.sleep(20)
            timeout += 20
        else:
            log("deploy-bundle: Applications in the bundle are not ready after {} seconds.".format(timeout))
            raise TidJujuK8sException("Timeout when deploying bundle")
        log("deploy-bundle: DONE")
    except TidJujuK8sException as toexception:
        log("deploy-bundle: TidJujuK8sException:" + str(toexception))
        action_fail('Timeout reached for deploying the bundle:' + str(toexception))
        log("deploy-bundle: DONE")
    except:
        log("Error. Command Failed.")
        action_fail('command failed:' + err)
        exc_type, exc_value, exc_traceback = sys.exc_info()
        err = traceback.format_exception(exc_type, exc_value, exc_traceback)
        log(str(err))
    else:
        action_set({'output': result})
    finally:
        clear_flag('actions.deploy-bundle')

@when('actions.undeploy-bundle')
def undeploy_bundle():
    err = ''
    try:
        cmd = "/snap/bin/juju machines --format yaml"
        log("undeploy-bundle: getting machines: " + cmd)
        result, err = charms.sshproxy._run(cmd)
        juju_machines = yaml.safe_load(result)

        n_machines = len(juju_machines['machines'])
        cmd = "chmod +x /home/ubuntu/undeploy-bundle.sh; /home/ubuntu/undeploy-bundle.sh > /dev/null && echo 'OK'"
        log("undeploy-bundle: command to execute: " + cmd)
        result, err = charms.sshproxy._run(cmd)
        log("undeploy-bundle: DONE")
    except:
        log("Error. Command Failed.")
        action_fail('command failed:' + err)
        exc_type, exc_value, exc_traceback = sys.exc_info()
        err = traceback.format_exception(exc_type, exc_value, exc_traceback)
        log(str(err))
    else:
        action_set({'output': result})
    finally:
        clear_flag('actions.undeploy-bundle')

@when('actions.remove-machines')
def remove_machines():
    err = ''
    try:
        force = action_get('force')

        cmd = "/snap/bin/juju machines --format yaml"
        log("remove-machines: getting machines: " + cmd)
        result, err = charms.sshproxy._run(cmd)
        juju_machines = yaml.safe_load(result)
        number_of_machines = len(juju_machines['machines'])

        #cfg = charms.sshproxy.get_config()
        #host = charms.sshproxy.get_host_ip()
        #user = cfg['ssh-username']
        #charms.sshproxy.sftp('scripts/remove-machine.sh', '/home/ubuntu/remove-machine.sh', host, user)

        for m in juju_machines['machines']:
            #cmd = "chmod +x /home/ubuntu/remove-machine.sh; /home/ubuntu/remove-machine.sh > /dev/null && echo 'OK'"
            cmd = "/snap/bin/juju remove-machine {}".format(m)
            if force:
                cmd += " --force"
            cmd += " > /dev/null && echo 'OK'"
            log("remove-machine: command to execute: " + cmd)
            result, err = charms.sshproxy._run(cmd)
        log("remove-machines: Checking whether all machines were removed")
        timeout = 0
        while timeout <= 600:
            try:
                started = 0
                cmd = "/snap/bin/juju machines --format yaml"
                log("remove-machines: getting machines: " + cmd)
                result, err = charms.sshproxy._run(cmd)
                if result:
                    juju_machines = yaml.safe_load(result)
                    n_machines = len(juju_machines['machines'])
                    log("remove-machines: {}/{} machines are active".format(n_machines,number_of_machines))
                    if n_machines == 0:
                        log("remove-machines: no machines".format(n_machines,number_of_machines))
                        break
                else:
                    log("remove-machines: no machines".format(n_machines,number_of_machines))
                    break
            except:
                log("Error. Command Failed." + str(err))
            time.sleep(20)
            timeout += 20
        else:
            log("remove-machines: Machines were not removed after {} seconds.".format(timeout))
            raise TidJujuK8sException("Timeout when adding machines")
        log("remove-machines: DONE")
    except:
        log("Error. Command Failed.")
        action_fail('command failed:' + err)
        exc_type, exc_value, exc_traceback = sys.exc_info()
        err = traceback.format_exception(exc_type, exc_value, exc_traceback)
        log(str(err))
    else:
        action_set({'output': result})
    finally:
        clear_flag('actions.remove-machines')

@when('actions.post-deploy')
def post_deploy():
    err = ''
    try:
        cfg = charms.sshproxy.get_config()
        host = charms.sshproxy.get_host_ip()
        user = cfg['ssh-username']
        charms.sshproxy.sftp('scripts/post-deploy.sh', '/home/ubuntu/post-deploy.sh', host, user)

        cmd = "chmod +x /home/ubuntu/post-deploy.sh; /home/ubuntu/post-deploy.sh > /dev/null && echo 'OK'"
        log("post-deploy: command to execute: " + cmd)
        result, err = charms.sshproxy._run(cmd)
        log("post-deploy: DONE")
    except:
        log("Error. Command Failed.")
        action_fail('command failed:' + err)
        exc_type, exc_value, exc_traceback = sys.exc_info()
        err = traceback.format_exception(exc_type, exc_value, exc_traceback)
        log(str(err))
    else:
        action_set({'output': result})
    finally:
        clear_flag('actions.post-deploy')

@when('actions.init-helm')
def init_helm():
    err = ''
    try:
        cfg = charms.sshproxy.get_config()
        host = charms.sshproxy.get_host_ip()
        user = cfg['ssh-username']
        charms.sshproxy.sftp('scripts/init-helm.sh', '/home/ubuntu/init-helm.sh', host, user)

        cmd = "chmod +x /home/ubuntu/init-helm.sh; /home/ubuntu/init-helm.sh > /dev/null && echo 'OK'"
        log("init-helm: command to execute: " + cmd)
        result, err = charms.sshproxy._run(cmd)
        log("init-helm: DONE")
    except:
        log("Error. Command Failed.")
        action_fail('command failed:' + err)
        exc_type, exc_value, exc_traceback = sys.exc_info()
        err = traceback.format_exception(exc_type, exc_value, exc_traceback)
        log(str(err))
    else:
        action_set({'output': result})
    finally:
        clear_flag('actions.init-helm')

@when('actions.install-openebs-chart')
def install_openebs_chart():
    err = ''
    try:
        cfg = charms.sshproxy.get_config()
        host = charms.sshproxy.get_host_ip()
        user = cfg['ssh-username']
        charms.sshproxy.sftp('scripts/openebs-storage-class.yaml', '/home/ubuntu/openebs-storage-class.yaml', host, user)

        cfg = charms.sshproxy.get_config()
        host = charms.sshproxy.get_host_ip()
        user = cfg['ssh-username']
        charms.sshproxy.sftp('scripts/install-openebs-chart.sh', '/home/ubuntu/install-openebs-chart.sh', host, user)

        cmd = "chmod +x /home/ubuntu/install-openebs-chart.sh; /home/ubuntu/install-openebs-chart.sh > /dev/null && echo 'OK'"
        log("install-openebs-chart: command to execute: " + cmd)
        result, err = charms.sshproxy._run(cmd)
        log("install-openebs-chart: DONE")
    except:
        log("Error. Command Failed.")
        action_fail('command failed:' + err)
        exc_type, exc_value, exc_traceback = sys.exc_info()
        err = traceback.format_exception(exc_type, exc_value, exc_traceback)
        log(str(err))
    else:
        action_set({'output': result})
    finally:
        clear_flag('actions.install-openebs-chart')

@when('actions.install-chart')
def install_chart():
    err = ''
    try:
        chart = action_get('chart')
        name = action_get('name')
        atomic = action_get('atomic')
        values = action_get('values')
        valuesFile = action_get('valuesFile')

        #cfg = charms.sshproxy.get_config()
        #host = charms.sshproxy.get_host_ip()
        #user = cfg['ssh-username']
        #charms.sshproxy.sftp('scripts/install-chart.sh', '/home/ubuntu/install-chart.sh', host, user)

        #cmd = "chmod +x /home/ubuntu/install-chart.sh; /home/ubuntu/install-chart.sh > /dev/null && echo 'OK'"
        cmd = "/snap/bin/helm install {} -n {}"
        if atomic:
            cmd += " --atomic"
        if values:
            with open("scripts/bundle-empty.yaml", 'r') as stream:
                try:
                    bundle_dict = yaml.safe_load(stream)
                except yaml.YAMLError as exc:
                    raise TidJujuK8sException("Error in the provided bundle: " + str(exc))
            yaml.safe_load(values)
        # -f ${VALUES_FILE} --atomic ${ADDITIONAL_OPTS}
        log("install-chart: command to execute: " + cmd)
        result, err = charms.sshproxy._run(cmd)
        log("install-chart: DONE")
    except:
        log("Error. Command Failed.")
        action_fail('command failed:' + err)
        exc_type, exc_value, exc_traceback = sys.exc_info()
        err = traceback.format_exception(exc_type, exc_value, exc_traceback)
        log(str(err))
    else:
        action_set({'output': result})
    finally:
        clear_flag('actions.install-chart')

@when('actions.upgrade-release')
def upgrade_release():
    err = ''
    try:
        chart = action_get('chart')
        name = action_get('name')
        atomic = action_get('atomic')
        values = action_get('values')
        valuesFile = action_get('valuesFile')

        cfg = charms.sshproxy.get_config()
        host = charms.sshproxy.get_host_ip()
        user = cfg['ssh-username']
        charms.sshproxy.sftp('scripts/upgrade-release.sh', '/home/ubuntu/upgrade-release.sh', host, user)

        cmd = "chmod +x /home/ubuntu/upgrade-release.sh; /home/ubuntu/upgrade-release.sh > /dev/null && echo 'OK'"
        log("upgrade-release: command to execute: " + cmd)
        result, err = charms.sshproxy._run(cmd)
        log("upgrade-release: DONE")
    except:
        log("Error. Command Failed.")
        action_fail('command failed:' + err)
        exc_type, exc_value, exc_traceback = sys.exc_info()
        err = traceback.format_exception(exc_type, exc_value, exc_traceback)
        log(str(err))
    else:
        action_set({'output': result})
    finally:
        clear_flag('actions.upgrade-release')

@when('actions.rollback-release')
def rollback_release():
    err = ''
    try:
        name = action_get('name')
        revision = action_get('revision')

        cfg = charms.sshproxy.get_config()
        host = charms.sshproxy.get_host_ip()
        user = cfg['ssh-username']
        charms.sshproxy.sftp('scripts/rollback-release.sh', '/home/ubuntu/rollback-release.sh', host, user)

        cmd = "chmod +x /home/ubuntu/rollback-release.sh; /home/ubuntu/rollback-release.sh > /dev/null && echo 'OK'"
        log("rollback-release: command to execute: " + cmd)
        result, err = charms.sshproxy._run(cmd)
        log("rollback-release: DONE")
    except:
        log("Error. Command Failed.")
        action_fail('command failed:' + err)
        exc_type, exc_value, exc_traceback = sys.exc_info()
        err = traceback.format_exception(exc_type, exc_value, exc_traceback)
        log(str(err))
    else:
        action_set({'output': result})
    finally:
        clear_flag('actions.rollback-release')

@when('actions.delete-release')
def delete_release():
    err = ''
    try:
        name = action_get('name')

        cfg = charms.sshproxy.get_config()
        host = charms.sshproxy.get_host_ip()
        user = cfg['ssh-username']
        charms.sshproxy.sftp('scripts/delete-release.sh', '/home/ubuntu/delete-release.sh', host, user)

        cmd = "chmod +x /home/ubuntu/delete-release.sh; /home/ubuntu/delete-release.sh > /dev/null && echo 'OK'"
        log("delete-release: command to execute: " + cmd)
        result, err = charms.sshproxy._run(cmd)
        log("delete-release: DONE")
    except:
        log("Error. Command Failed.")
        action_fail('command failed:' + err)
        exc_type, exc_value, exc_traceback = sys.exc_info()
        err = traceback.format_exception(exc_type, exc_value, exc_traceback)
        log(str(err))
    else:
        action_set({'output': result})
    finally:
        clear_flag('actions.delete-release')

@when('actions.add-repo')
def add_repo():
    err = ''
    try:
        name = action_get('name')
        url = action_get('url')

        #cfg = charms.sshproxy.get_config()
        #host = charms.sshproxy.get_host_ip()
        #user = cfg['ssh-username']
        #charms.sshproxy.sftp('scripts/add-repo.sh', '/home/ubuntu/add-repo.sh', host, user)

        #cmd = "chmod +x /home/ubuntu/add-repo.sh; /home/ubuntu/add-repo.sh > /dev/null && echo 'OK'"
        cmd = "/snap/bin/helm repo add {} {} > /dev/null && /snap/bin/helm repo update > /dev/null && echo 'OK'".format(name,url)
        log("add-repo: command to execute: " + cmd)
        result, err = charms.sshproxy._run(cmd)
        log("add-repo: DONE")
    except:
        log("Error. Command Failed.")
        action_fail('command failed:' + err)
        exc_type, exc_value, exc_traceback = sys.exc_info()
        err = traceback.format_exception(exc_type, exc_value, exc_traceback)
        log(str(err))
    else:
        action_set({'output': result})
    finally:
        clear_flag('actions.add-repo')

@when('actions.remove-repo')
def remove_repo():
    err = ''
    try:
        name = action_get('name')

        #cfg = charms.sshproxy.get_config()
        #host = charms.sshproxy.get_host_ip()
        #user = cfg['ssh-username']
        #charms.sshproxy.sftp('scripts/remove-repo.sh', '/home/ubuntu/remove-repo.sh', host, user)

        #cmd = "chmod +x /home/ubuntu/remove-repo.sh; /home/ubuntu/remove-repo.sh > /dev/null && echo 'OK'"
        cmd = "/snap/bin/helm repo remove {} > /dev/null && /snap/bin/helm repo update > /dev/null && echo 'OK'".format(name)
        log("remove-repo: command to execute: " + cmd)
        result, err = charms.sshproxy._run(cmd)
        log("remove-repo: DONE")
    except:
        log("Error. Command Failed.")
        action_fail('command failed:' + err)
        exc_type, exc_value, exc_traceback = sys.exc_info()
        err = traceback.format_exception(exc_type, exc_value, exc_traceback)
        log(str(err))
    else:
        action_set({'output': result})
    finally:
        clear_flag('actions.delete-release')


