{{- define "signatrust.annotations" -}}
{{- range $k, $v := .Values.global.commonAnnotations }}
{{ $k }}: {{ $v | quote }}
{{- end }}
{{- end -}}
