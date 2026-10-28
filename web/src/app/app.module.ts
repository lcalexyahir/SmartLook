// web/src/app/app.module.ts
//
// Único cambio: se agrega el provider DATE_PIPE_DEFAULT_OPTIONS con
// timezone '-0400' (Bolivia, sin horario de verano, offset fijo todo el
// año). Con esto, CUALQUIER uso de "| date" en toda la aplicación
// muestra la hora en horario boliviano automáticamente, sin tener que
// especificar ':-0400' pantalla por pantalla.
// NUEVO (SaaS - A.3): se registra PlanInterceptor, que muestra en el panel los
// errores de plan (403 plan_no_permitido y 402 suscripcion_vencida).
// NUEVO (SaaS - A.6 PWA): registra el service worker (la aplicación se puede
// instalar y abrir sin conexión) y OfflineCacheInterceptor (copia local del
// catálogo, disponibilidad y reservas para consultarlos sin internet).
// El service worker no se registra con "ng serve" (puerto 4200), donde no
// existe ngsw-worker.js; sí en el build que se sirve en local y en Render.
import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { HttpClientModule, HTTP_INTERCEPTORS } from '@angular/common/http';
import { ReactiveFormsModule } from '@angular/forms';
import { DATE_PIPE_DEFAULT_OPTIONS } from '@angular/common';
import { ServiceWorkerModule } from '@angular/service-worker';
import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';
import { LayoutComponent } from './layout/layout.component';
import { JwtInterceptor } from './core/auth/jwt.interceptor';
import { PlanInterceptor } from './core/interceptors/plan.interceptor';
import { OfflineCacheInterceptor } from './core/interceptors/offline-cache.interceptor';
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
    AppRoutingModule,
    ServiceWorkerModule.register('ngsw-worker.js', {
      enabled: location.port !== '4200',
      registrationStrategy: 'registerImmediately'
    })
  ],
  providers: [
    {
      provide: HTTP_INTERCEPTORS,
      useClass: JwtInterceptor,
      multi: true
    },
    {
      provide: HTTP_INTERCEPTORS,
      useClass: PlanInterceptor,
      multi: true
    },
    {
      provide: HTTP_INTERCEPTORS,
      useClass: OfflineCacheInterceptor,
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