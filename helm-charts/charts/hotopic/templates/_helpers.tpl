{{/*
Application name
*/}}
{{- define "hotopic.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Full application name
*/}}
{{- define "hotopic.fullname" -}}
{{- default .Release.Name .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "hotopic.labels" -}}
app.kubernetes.io/name: {{ include "hotopic.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "hotopic.selectorLabels" -}}
app.kubernetes.io/name: {{ include "hotopic.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

