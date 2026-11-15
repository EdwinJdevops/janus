package main

import (
 "context"
 "net/http"
 "net/http/httptest"
 "testing"
 "time"
)
func TestProbe429(t *testing.T){
 count:=0
 s:=httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter,r *http.Request){count++;w.WriteHeader(http.StatusTooManyRequests)}));defer s.Close()
 if err:=run(context.Background(),s.Client(),s.URL,3,0);err!=nil{t.Fatal(err)}
 if count!=3{t.Fatalf("expected 3 explicit requests, got %d",count)}
}
func TestRejectInvalidArguments(t *testing.T){
 if err:=run(context.Background(),&http.Client{},"http://localhost",0,time.Second);err==nil{t.Fatal("expected error")}
}
