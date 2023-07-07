# check_cpu_utilization.ps1.py
Monitoring plugin that uses Windows Performance Counters to evaluate CPU Utilization to be used with NagiosXI Windows_SSH based service checks.

# DESCRIPTION
A PowerShell based plugin for Nagios and Nagios-like systems. This plugin checks the CPU utilization on Windows machines via evaluation of the Process Performce Counters. 
This plugin gives you the CPU Utilization for the system, across all cores.
Remember, thresholds violations result when a metric value is "equal to or greater than" the threshold provided.
E.g. -warning 10 will need the number of files to be equal to 10 or higher to throw a WARNING.

## SYNOPSIS
- A PowerShell based plugin to check CPU Utilization via Windows Processor Performance Counters

## NOTES
- This plugin will return performance data.

## POWERSHELL PARAMETERS

### metric
- The Processor Metric you would like to evaluate. User = Percent User Time (Default), Proc = Percent Processor Time, Priv = Percent Privileged Time 

### warning
- The CPU utilization you will tolerate before throwing a WARNING

### critical
- The CPU utilization you will tolerate before throwing a CRITICAL

## EMBEDED POWERSHELL EXAMPLES
- PS> .\check_cpu_utilization.ps1
- PS> .\check_cpu_utilization.ps1 -metric Proc -warning 80 -critical 90
- PS> .\check_cpu_utilization.ps1 -metric User -warning 80 -critical 90
- PS> .\check_cpu_utilization.ps1 -metric Priv -warning 80 -critical 90
