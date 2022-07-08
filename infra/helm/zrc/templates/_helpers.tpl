{{/*
Expand the name of the chart.
*/}}
{{- define "postgres.name" -}}
{{- if .Values.postgresNameOverride }}
{{- .Values.postgresNameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := "postgres" -}}
{{- printf "%s" $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}

{{- define "zakenapi.name" -}}
{{- if .Values.zakenAPiNameOverride }}
{{- .Values.zakenAPiNameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := "zakenapi" -}}
{{- printf "%s" $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "postgres.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "zrc.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "zrc.labels" -}}
helm.sh/chart: {{ include "zrc.chart" . }}
{{ include "postgres.selectorLabels" . }}
{{- if .Values.config.environment }}
app.kubernetes.io/env: {{ .Values.config.environment }}
{{- end }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "postgres.selectorLabels" -}}
app.kubernetes.io/name: {{ include "postgres.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "zakenapi.selectorLabels" -}}
app.kubernetes.io/name: {{ include "zakenapi.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "postgres.selector" -}}
app: postgis
{{- end }}

{{- define "zrc.namespace" -}}
  {{- if .Values.namespaceOverride -}}
    {{- .Values.namespaceOverride -}}
  {{- else -}}
    {{- .Release.Namespace -}}
  {{- end -}}
{{- end -}}


{{- define "postgres.secretName" -}}
{{- $name := "secret" }}
  {{- if .Values.secretName -}}
    {{- .Values.secretName -}}
  {{- else -}}
    {{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
  {{- end -}}
{{- end -}}

{{- define "postgres.serviceName" -}}
{{- if .Values.postgresServiceNameOverride }}
{{- .Values.postgresServiceNameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := "postgres" -}}
{{- printf "%s" $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}

{{- define "zakenapi.serviceName" -}}
{{- if .Values.zakenapiServiceNameOverride }}
{{- .Values.zakenapiServiceNameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := "zakenapi" -}}
{{- printf "%s" $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}


{{- define "postgres.storageClassName" -}}
  {{- $name := "test" }}
  {{- if eq .Values.config.environment "minikube" }}
    {{- $name = "standard" }}
  {{- else if eq .Values.config.environment "docker-desktop" -}}
    {{- $name = "hostpath" }}
  {{- else -}}
    {{- $name = "unknownEnv" }}
  {{- end -}}
  {{- printf "%s" $name | trunc 63 | trimSuffix "-" }}
{{- end -}}
