import { Injectable } from '@angular/core';
import {
  HttpInterceptor,
  HttpRequest,
  HttpHandler,
  HttpEvent
} from '@angular/common/http';

import { Observable } from 'rxjs';


@Injectable()
export class JwtInterceptor implements HttpInterceptor {


  intercept(
    req: HttpRequest<any>,
    next: HttpHandler
  ): Observable<HttpEvent<any>> {


    const token = localStorage.getItem('access_token');


    if (!token) {

      return next.handle(req);

    }


    const authReq = req.clone({

      setHeaders: {

        Authorization: `Bearer ${token}`

      }

    });


    return next.handle(authReq);

  }

}