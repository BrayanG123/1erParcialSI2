import { Component, inject, AfterViewInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import maplibregl from 'maplibre-gl';
import { TallerService } from '../../../talleres/services/taller.service';
import { AuthService } from '../../../../core/auth/services/auth.service';

@Component({
  selector: 'app-setup-taller',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './setup-taller.component.html',
  styleUrls: ['./setup-taller.component.css']
})
export class SetupTallerComponent implements AfterViewInit, OnDestroy {
  private fb = inject(FormBuilder);
  private tallerService = inject(TallerService);
  private authService = inject(AuthService);
  private router = inject(Router);

  private http = inject(HttpClient);

  isSubmitting = false;
  errorMessage = '';
  locationSelected = false;
  gpsLoading = true;

  // Dirección obtenida automáticamente de la ubicación marcada en el mapa
  // (geocodificación inversa con Nominatim/OpenStreetMap)
  direccionDetectada = '';
  buscandoDireccion = false;

  private map!: maplibregl.Map;
  private marker!: maplibregl.Marker;

  setupForm = this.fb.nonNullable.group({
    nombre:    ['', [Validators.required, Validators.minLength(3)]],
    // La dirección ya no se escribe a mano: se llena sola al marcar el mapa
    direccion: [''],
    telefono:  ['', [Validators.required]],
    latitud:   [0, [Validators.required]],
    longitud:  [0, [Validators.required]]
  });

  ngAfterViewInit() {
    setTimeout(() => this.initMap(), 100);
  }

  ngOnDestroy() {
    if (this.map) this.map.remove();
  }

  private initMap() {
    this.map = new maplibregl.Map({
      container: 'taller-map',
      style: 'https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json', // colorido
      center: [-63.1812, -17.7833],  // Santa Cruz de la Sierra [lng, lat]
      zoom: 13
    });

    this.map.addControl(new maplibregl.NavigationControl(), 'top-right');

    this.map.on('load', () => {
      if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
          (pos) => {
            const { latitude, longitude } = pos.coords;
            this.map.flyTo({ center: [longitude, latitude], zoom: 16 });
            this.placeMarker(longitude, latitude);
            this.gpsLoading = false;
          },
          () => {
            this.gpsLoading = false;
          },
          { timeout: 8000 }
        );
      } else {
        this.gpsLoading = false;
      }
    });

    this.map.on('click', (e: maplibregl.MapMouseEvent) => {
      const { lng, lat } = e.lngLat;
      this.placeMarker(lng, lat);
    });
  }

  private placeMarker(lng: number, lat: number) {
    if (this.marker) {
      this.marker.setLngLat([lng, lat]);
    } else {
      // Pin personalizado visible
      const el = document.createElement('div');
      el.style.cssText = `
        width: 28px;
        height: 28px;
        background: #4f46e5;
        border: 3px solid white;
        border-radius: 50% 50% 50% 0;
        transform: rotate(-45deg);
        box-shadow: 0 2px 8px rgba(79,70,229,0.5);
        cursor: grab;
      `;

      this.marker = new maplibregl.Marker({ element: el, draggable: true })
        .setLngLat([lng, lat])
        .setPopup(
          new maplibregl.Popup({ offset: 30 })
            .setText('📍 Ubicación del taller')
        )
        .addTo(this.map);

      this.marker.on('dragend', () => {
        const pos = this.marker.getLngLat();
        this.updateCoords(pos.lat, pos.lng);
      });
    }

    this.updateCoords(lat, lng);
  }

  private updateCoords(lat: number, lng: number) {
    this.setupForm.patchValue({ latitud: lat, longitud: lng });
    this.locationSelected = true;
    this.obtenerDireccion(lat, lng);
  }

  /**
   * Geocodificación inversa: convierte las coordenadas marcadas en una
   * dirección legible usando Nominatim (OpenStreetMap, gratis, sin clave).
   * Si falla (sin internet, rate limit), usa las coordenadas como dirección.
   */
  private obtenerDireccion(lat: number, lng: number) {
    // Fallback inmediato: si Nominatim falla, esto es lo que se guarda
    const fallback = `Lat ${lat.toFixed(5)}, Lng ${lng.toFixed(5)}`;
    this.setupForm.patchValue({ direccion: fallback });

    this.buscandoDireccion = true;
    this.http.get<any>(
      `https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${lat}&lon=${lng}&accept-language=es`
    ).subscribe({
      next: (res) => {
        this.buscandoDireccion = false;
        if (res?.display_name) {
          // Recortar a un largo razonable para la columna de la BD (500)
          const direccion = String(res.display_name).slice(0, 480);
          this.direccionDetectada = direccion;
          this.setupForm.patchValue({ direccion });
        } else {
          this.direccionDetectada = fallback;
        }
      },
      error: () => {
        this.buscandoDireccion = false;
        this.direccionDetectada = fallback;
      }
    });
  }

  onSubmit() {
    if (this.setupForm.valid && this.locationSelected) {
      this.isSubmitting = true;
      this.errorMessage = '';

      this.tallerService.registrarTaller(this.setupForm.getRawValue()).subscribe({
        next: () => {
          this.isSubmitting = false;
          localStorage.setItem('has_taller', 'true');
          this.router.navigate(['/admin/dashboard']);
        },
        error: (err: any) => {
          this.isSubmitting = false;
          this.errorMessage = err.error?.detail || 'Error al configurar el taller.';
        }
      });
    }
  }

  logout() {
    this.authService.logout();
  }
}
