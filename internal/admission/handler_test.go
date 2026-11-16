package admission

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
)

func TestAdmissionReviewDenialContract(t *testing.T) {
	request := httptest.NewRequest(http.MethodPost, "/validate", strings.NewReader(`{"apiVersion":"admission.k8s.io/v1","kind":"AdmissionReview","request":{"uid":"test-uid"}}`))
	recorder := httptest.NewRecorder()
	Handler(recorder, request)
	if recorder.Code != http.StatusOK {
		t.Fatalf("HTTP status = %d, want 200 (transport)", recorder.Code)
	}
	var out Review
	if err := json.Unmarshal(recorder.Body.Bytes(), &out); err != nil {
		t.Fatal(err)
	}
	if out.Response == nil || out.Response.UID != "test-uid" || out.Response.Allowed || out.Response.Result == nil || out.Response.Result.Code != 429 {
		t.Fatalf("unexpected admission response: %+v", out.Response)
	}
}

func TestAdmissionReviewInvalidRequest(t *testing.T) {
	for _, test := range []struct {
		method, body string
		want         int
	}{
		{http.MethodGet, "", 405},
		{http.MethodPost, "{", 400},
		{http.MethodPost, `{"apiVersion":"admission.k8s.io/v1","kind":"AdmissionReview"}`, 400},
	} {
		r := httptest.NewRequest(test.method, "/validate", strings.NewReader(test.body))
		w := httptest.NewRecorder()
		Handler(w, r)
		if w.Code != test.want {
			t.Fatalf("got %d want %d", w.Code, test.want)
		}
	}
}

func TestRejectTrailingJSON(t *testing.T) {
	request := httptest.NewRequest(http.MethodPost, "/validate", strings.NewReader(`{"apiVersion":"admission.k8s.io/v1","kind":"AdmissionReview","request":{"uid":"x"}} {"extra":true}`))
	recorder := httptest.NewRecorder()
	Handler(recorder, request)
	if recorder.Code != http.StatusBadRequest {
		t.Fatalf("got %d want 400", recorder.Code)
	}
}
