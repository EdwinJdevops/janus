package admission

import (
	"encoding/json"
	"io"
	"net/http"
)

type Review struct {
	APIVersion string `json:"apiVersion"`
	Kind       string `json:"kind"`
	Request    *struct {
		UID string `json:"uid"`
	} `json:"request,omitempty"`
	Response *Response `json:"response,omitempty"`
}

type Response struct {
	UID     string  `json:"uid"`
	Allowed bool    `json:"allowed"`
	Result  *Status `json:"status,omitempty"`
}

type Status struct {
	Code    int32  `json:"code"`
	Message string `json:"message"`
}

// Handler deliberately rejects admission requests for a synthetic contract test.
// It is not an overload-control mechanism and must never be deployed to a cluster.
func Handler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "POST required", http.StatusMethodNotAllowed)
		return
	}
	r.Body = http.MaxBytesReader(w, r.Body, 1<<20)
	defer r.Body.Close()
	var in Review
	if err := json.NewDecoder(r.Body).Decode(&in); err != nil {
		http.Error(w, "invalid AdmissionReview", http.StatusBadRequest)
		return
	}
	var extra any
	if err := json.NewDecoder(r.Body).Decode(&extra); err != io.EOF {
		http.Error(w, "trailing AdmissionReview data", http.StatusBadRequest)
		return
	}
	if in.Request == nil || in.Request.UID == "" || in.APIVersion != "admission.k8s.io/v1" || in.Kind != "AdmissionReview" {
		http.Error(w, "invalid AdmissionReview metadata", http.StatusBadRequest)
		return
	}
	out := Review{APIVersion: "admission.k8s.io/v1", Kind: "AdmissionReview", Response: &Response{UID: in.Request.UID, Allowed: false, Result: &Status{Code: 429, Message: "synthetic rejection for test only"}}}
	w.Header().Set("Content-Type", "application/json")
	_ = json.NewEncoder(w).Encode(out)
}
