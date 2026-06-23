{{/*
Expand the name of the chart.
*/}}
{{- define "ascend-runner-onboarding.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "ascend-runner-onboarding.fullname" -}}
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
Common labels
*/}}
{{- define "ascend-runner-onboarding.labels" -}}
helm.sh/chart: {{ include "ascend-runner-onboarding.fullname" . }}
{{ include "ascend-runner-onboarding.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "ascend-runner-onboarding.selectorLabels" -}}
app.kubernetes.io/name: {{ include "ascend-runner-onboarding.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}
