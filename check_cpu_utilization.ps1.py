#!/usr/bin/env python3
import sys
from sys import argv
from subprocess import Popen
from subprocess import PIPE
import argparse

argument_parser = argparse.ArgumentParser()

argument_parser.add_argument( '-H',
                     '--host',
                     required=True,
                     type=str,
                     help='The host you wish to run a plugin against.')

argument_parser.add_argument( '-u',
                     '--user',
                     required=True,
                     type=str,
                     help='Username for connecting to the remote system.')


argument_parser.add_argument( '-a',
                     '--args',
                     required=False,
                     type=str,
                     help='Arguments to be sent to the plugin. e.g. -warning 80 -critical 90'
)

arguments = argument_parser.parse_args(argv[1:])
plugin_code = """
<#
.DESCRIPTION
A PowerShell based plugin for Nagios and Nagios-like systems. This plugin checks the CPU utilization on Windows machines via evaluation of the Process Performce Counters. 
This plugin gives you the CPU Utilization for the system, across all cores.
Remember, thresholds violations result when a metric value is "equal to or greater than" the threshold provided.
E.g. -warning 10 will need the number of files to be equal to 10 or higher to throw a WARNING.
.SYNOPSIS
A PowerShell based plugin to check CPU Utilization via Windows Processor Performance Counters
.NOTES
This plugin will return performance data.
.PARAMETER metric
The Processor Metric you would like to evaluate. User = Percent User Time (Default), Proc = Percent Processor Time, Priv = Percent Privileged Time 
.PARAMETER warning
The CPU utilization you will tolerate before throwing a WARNING
.PARAMETER critical
The CPU utilization you will tolerate before throwing a CRITICAL
.EXAMPLE
PS> .\check_cpu_utilization.ps1
.EXAMPLE
PS> .\check_cpu_utilization.ps1 -metric Proc -warning 80 -critical 90
.EXAMPLE
PS> .\check_cpu_utilization.ps1 -metric User -warning 80 -critical 90
.EXAMPLE
PS> .\check_cpu_utilization.ps1 -metric Priv -warning 80 -critical 90
#>

#SCRIPT INPUT
param(
    [Parameter(Mandatory = $false)][ValidateSet('Proc', 'User', 'Priv')][string]$metric = 'User',
    [Parameter(Mandatory=$false)][int]$warning = $null,
    [Parameter(Mandatory=$false)][int]$critical = $null
)

#SANITY VARS
$message = "Nothing changed the status output!"
$exitcode = 3

#EVALUATE THE DATA
function processCheck {
    param (
        [Parameter(Mandatory=$true)][int]$checkResult,
        [Parameter(Mandatory=$true)][int]$warningThresh,
        [Parameter(Mandatory=$true)][int]$criticalThresh,
        [Parameter(Mandatory=$false)][string]$returnMessage
    )

    [array]$returnArray
    if ((!$criticalThresh) -and (!$warningThresh)) {
        $returnArray = @(0, "OK: $returnMessage")
    }
    elseif ($checkResult -ge $criticalThresh) {
        $returnArray = @(2, "CRITICAL: $returnMessage")
    }
    elseif (($checkResult -ge $warningThresh) -and ($checkResult -lt $criticalThresh)) {
        $returnArray = @(1, "WARNING: $returnMessage")
    }
    else {
        $returnArray = @(0, "OK: $returnMessage")
    }

    return $returnArray
}

#GET THE WINDOWS COUTNER DATA BASED UPON METRIC
if($metric -eq "User"){
    #METRICNAME
    $metricName = "\Processor(_Total)\% User Time"
    #PERFNAME
    $metricSafeName = "ProcessorUserTime"
}
elseif($metric -eq "Proc"){
    #METRICNAME
    $metricName = "\Processor(_Total)\% Processor Time"
    #PERFNAME
    $metricSafeName = "ProcessorTotalTime"
}
elseif($metric = 'Priv'){
    #METRICNAME
    $metricName = "\Processor(_Total)\% Privileged Time"
    #PERFNAME
    $metricSafeName = "ProcessorPrivilegedTime"
    
}

#METRIC
$metricData = (Get-Counter -Counter "$metricName" -SampleInterval 1 -MaxSamples 1).CounterSamples.CookedValue

#FORMAT
$metricData = [math]::Round($metricdata)

#RUN THE CHECK
$processArray = processCheck -checkResult $metricData `
                             -warningThresh $warning `
                             -criticalThresh $critical `
                             -returnMessage "$metricName is $metricData% | '$metricSafeName'=$metricData%;$warning;$critical"
#NAGIOS EXIT
$exitcode = $processArray[1]
$exitMessage = $processArray[2]
write-host "$exitMessage,$exitcode"

#SYSTEM EXIT (USE LAST EXIT CODE)
exit $exitcode

"""
echo_process = ""
arguments_length = 0
if arguments.args is not None:
    echo_process = Popen(["echo", "function checkplugin {\n", plugin_code, " }\n", "checkplugin ", arguments.args, "\n"], stdout=PIPE)
    arguments_length = len(arguments.args) + 1
else:
    echo_process = Popen(["echo", "function checkplugin {\n", plugin_code, " }\n", "checkplugin  \n"], stdout=PIPE)

ssh_process = Popen(["ssh", "-T", "-l", arguments.user, arguments.host, "powershell.exe"], stdin=echo_process.stdout, stdout=PIPE)
echo_process.stdout.close()
process_output = [ssh_process.communicate(), ssh_process.returncode]

decoded_stdout = process_output[0][0].decode()

if(process_output[1] == 255):
    print("CRITICAL: Connection to host failed. Check that the nagios user can passwordlessly connect to the host.")
    sys.exit(2)     

output_substring = decoded_stdout[(decoded_stdout.find("checkplugin  ") + 18 + arguments_length):(len(decoded_stdout) - 1)].rstrip()
split_output_substring = output_substring.split(',')

exit_status_code = int(split_output_substring[-1])
exit_message = ','.join(split_output_substring[:-1]) 
print(exit_message)
sys.exit(exit_status_code)