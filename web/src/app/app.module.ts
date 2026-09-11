// web/src/app/app.module.ts
//
// Único cambio: se agrega el provider DATE_PIPE_DEFAULT_OPTIONS con
// timezone '-0400' (Bolivia, sin horario de verano, offset fijo todo el
// año). Con esto, CUALQUIER uso de "| date" en toda la aplicación
// muestra la hora en horario boliviano automáticamente, sin tener que
// especificar ':-0400' pantalla por pantalla.

import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { HttpClientModule, HTTP_INTERCEPTORS } from '@angular/common/http';
import { ReactiveFormsModule } from '@angular/forms';
import { DATE_PIPE_DEFAULT_OPTIONS } from '@angular/common';
import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';
import { LayoutComponent } from './layout/layout.component';
import { JwtInterceptor } from './core/auth/jwt.interceptor';


@NgModule({

  declarations: [
  AppComponent,
  LayoutComponent
],

  imports: [
    BrowserModule,
    BrowserAnimationsModule,
    HttpClientModule,
    ReactiveFormsModule,
    AppRoutingModule
  ],

  providers: [

    {
      provide: HTTP_INTERCEPTORS,
      useClass: JwtInterceptor,
      multi: true
    },

    {
      provide: DATE_PIPE_DEFAULT_OPTIONS,
      useValue: { timezone: '-0400' }
    }

  ],

  bootstrap: [
    AppComponent
  ]

})

export class AppModule { }