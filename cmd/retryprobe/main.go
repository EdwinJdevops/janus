package main

import (
 "context"
 "encoding/json"
 "errors"
 "flag"
 "fmt"
 "net/http"
 "os"
 "time"
)

type record struct { Time string `json:"time"`; Attempt int `json:"attempt"`; Status int `json:"status,omitempty"`; DurationMS int64 `json:"duration_ms"`; Error string `json:"error,omitempty"` }
func run(ctx context.Context, client *http.Client, endpoint string, attempts int, interval time.Duration) error {
 if attempts < 1 || interval < 0 { return errors.New("invalid attempts or interval") }
 encoder:=json.NewEncoder(os.Stdout)
 for i:=1;i<=attempts;i++ {
  if i>1 { select {case <-ctx.Done(): return ctx.Err(); case <-time.After(interval):} }
  req,err:=http.NewRequestWithContext(ctx,http.MethodGet,endpoint,nil); if err!=nil{return err}
  start:=time.Now();resp,err:=client.Do(req)
  rec:=record{Time:start.UTC().Format(time.RFC3339Nano),Attempt:i,DurationMS:time.Since(start).Milliseconds()}
  if err!=nil {rec.Error=err.Error()} else {rec.Status=resp.StatusCode;resp.Body.Close()}
  if err:=encoder.Encode(rec);err!=nil{return err}
 }
 return nil
}
func main(){
 endpoint:=flag.String("url","","HTTPS endpoint to probe; no credentials are sent")
 attempts:=flag.Int("attempts",3,"number of GET requests")
 interval:=flag.Duration("interval",time.Second,"delay between requests")
 timeout:=flag.Duration("timeout",5*time.Second,"per-request timeout")
 flag.Parse()
 if *endpoint==""||*timeout<=0 {fmt.Fprintln(os.Stderr,"-url and positive -timeout required");os.Exit(2)}
 client:=&http.Client{Timeout:*timeout,CheckRedirect:func(_ *http.Request,_ []*http.Request)error{return http.ErrUseLastResponse}}
 if err:=run(context.Background(),client,*endpoint,*attempts,*interval);err!=nil{fmt.Fprintln(os.Stderr,err);os.Exit(1)}
}
