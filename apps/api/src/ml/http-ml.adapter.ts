import { HttpService } from '@nestjs/axios';
import { Injectable, Logger } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { AxiosError } from 'axios';
import { firstValueFrom } from 'rxjs';
import {
  MlCue,
  MlEntityResult,
  MlJobStatus,
  MlPrediction,
  MlPdfResult,
  MlSegmentResult,
  MlServicePort,
  MlTrainRequest,
  MlTranscriptResult,
  MlTranscriptUnavailable,
  SegmentParams,
} from './ml-service.port';

/**
 * HttpMlAdapter — implementación HTTP del `MlServicePort`.
 *
 * Traduce las llamadas del dominio en peticiones al microservicio Python
 * (FastAPI). Es el único punto de NestJS que conoce el contrato HTTP del ML.
 */
@Injectable()
export class HttpMlAdapter implements MlServicePort {
  private readonly logger = new Logger(HttpMlAdapter.name);
  private readonly baseUrl: string;
  private readonly timeout: number;
  /** Auth interna: el servicio ML exige este header si ML_INTERNAL_TOKEN está definido. */
  private readonly headers: Record<string, string>;

  constructor(
    private readonly http: HttpService,
    private readonly config: ConfigService,
  ) {
    this.baseUrl = this.config.get<string>('ML_SERVICE_URL', 'http://localhost:8000');
    this.timeout = parseInt(this.config.get<string>('ML_TIMEOUT_MS', '600000'), 10);
    const token = this.config.get<string>('ML_INTERNAL_TOKEN');
    const modalKey = this.config.get<string>('MODAL_PROXY_TOKEN_ID');
    const modalSecret = this.config.get<string>('MODAL_PROXY_TOKEN_SECRET');
    this.headers = token ? { 'X-Internal-Token': token } : {};
    if (modalKey && modalSecret) {
      this.headers['Modal-Key'] = modalKey;
      this.headers['Modal-Secret'] = modalSecret;
    }
  }

  async health(): Promise<{ status: string }> {
    const { data } = await firstValueFrom(
      this.http.get(`${this.baseUrl}/health`, { timeout: 5000, headers: this.headers }),
    );
    return data;
  }

  async transcribeSubtitles(youtubeUrl: string, languages?: string[]): Promise<MlTranscriptResult> {
    try {
      const { data } = await firstValueFrom(
        this.http.post<MlTranscriptResult>(
          `${this.baseUrl}/transcribe`,
          { youtube_url: youtubeUrl, languages },
          { timeout: 60000, headers: this.headers },
        ),
      );
      return data;
    } catch (err) {
      const axiosErr = err as AxiosError;
      // 422 → el servicio ML no encontró subtítulos: señal para el fallback Whisper.
      if (axiosErr.response?.status === 422) {
        const detail = (axiosErr.response.data as { detail?: string })?.detail ?? 'sin subtítulos';
        throw new MlTranscriptUnavailable(detail);
      }
      throw this.wrap(err, 'transcribeSubtitles');
    }
  }

  async transcribeAudio(youtubeUrl: string, languages?: string[]): Promise<MlTranscriptResult> {
    try {
      const { data } = await firstValueFrom(
        this.http.post<MlTranscriptResult>(
          `${this.baseUrl}/transcribe/audio`,
          { youtube_url: youtubeUrl, languages },
          { timeout: this.timeout, headers: this.headers },
        ),
      );
      return data;
    } catch (err) {
      throw this.wrap(err, 'transcribeAudio');
    }
  }

  async segment(cues: MlCue[], params?: SegmentParams): Promise<MlSegmentResult> {
    try {
      const { data } = await firstValueFrom(
        this.http.post<MlSegmentResult>(
          `${this.baseUrl}/segment`,
          {
            cues,
            window_sec: params?.window_sec ?? 60,
            overlap_sec: params?.overlap_sec ?? 10,
          },
          { timeout: 60000, headers: this.headers },
        ),
      );
      return data;
    } catch (err) {
      throw this.wrap(err, 'segment');
    }
  }

  async extractPdf(content: Buffer, filename: string): Promise<MlPdfResult> {
    try {
      const form = new FormData();
      const bytes = content.buffer.slice(content.byteOffset, content.byteOffset + content.byteLength) as ArrayBuffer;
      form.append('file', new Blob([bytes], { type: 'application/pdf' }), filename);
      const { data } = await firstValueFrom(
        this.http.post<MlPdfResult>(`${this.baseUrl}/documents/pdf/extract`, form, {
          timeout: this.timeout,
          headers: this.headers,
        }),
      );
      return data;
    } catch (err) {
      throw this.wrap(err, 'extractPdf');
    }
  }

  async train(req: MlTrainRequest): Promise<{ job_id: string }> {
    try {
      const { data } = await firstValueFrom(
        this.http.post<{ job_id: string }>(`${this.baseUrl}/train`, req, { timeout: 60000, headers: this.headers }),
      );
      return data;
    } catch (err) {
      throw this.wrap(err, 'train');
    }
  }

  async getJob(jobId: string): Promise<MlJobStatus> {
    try {
      const { data } = await firstValueFrom(
        this.http.get<MlJobStatus>(`${this.baseUrl}/jobs/${jobId}`, { timeout: 15000, headers: this.headers }),
      );
      return data;
    } catch (err) {
      throw this.wrap(err, 'getJob');
    }
  }

  async loadModel(artifactPath: string): Promise<{ loaded: boolean; labels: string[] }> {
    try {
      const { data } = await firstValueFrom(
        this.http.post<{ loaded: boolean; labels: string[] }>(
          `${this.baseUrl}/models/load`,
          { artifact_path: artifactPath },
          { timeout: 120000, headers: this.headers },
        ),
      );
      return data;
    } catch (err) {
      throw this.wrap(err, 'loadModel');
    }
  }

  async infer(texts: string[]): Promise<MlPrediction[]> {
    try {
      const { data } = await firstValueFrom(
        this.http.post<{ predictions: MlPrediction[] }>(
          `${this.baseUrl}/infer`,
          { texts },
          { timeout: 120000, headers: this.headers },
        ),
      );
      return data.predictions;
    } catch (err) {
      throw this.wrap(err, 'infer');
    }
  }

  async embed(texts: string[]): Promise<{ model: string; dimensions: number; embeddings: number[][] }> {
    try {
      const { data } = await firstValueFrom(
        this.http.post<{ model: string; dimensions: number; embeddings: number[][] }>(
          `${this.baseUrl}/embeddings`,
          { texts },
          { timeout: this.timeout, headers: this.headers },
        ),
      );
      return data;
    } catch (err) {
      throw this.wrap(err, 'embed');
    }
  }

  async extractEntities(texts: string[]): Promise<MlEntityResult> {
    try {
      const { data } = await firstValueFrom(
        this.http.post<MlEntityResult>(
          `${this.baseUrl}/entities/extract`,
          { texts },
          { timeout: this.timeout, headers: this.headers },
        ),
      );
      return data;
    } catch (err) {
      throw this.wrap(err, 'extractEntities');
    }
  }

  private wrap(err: unknown, op: string): Error {
    const axiosErr = err as AxiosError;
    const status = axiosErr.response?.status;
    const detail = (axiosErr.response?.data as { detail?: string })?.detail ?? axiosErr.message;
    this.logger.error(`ML ${op} falló (${status ?? 'sin respuesta'}): ${detail}`);
    return new Error(`Servicio ML: ${op} falló: ${detail}`);
  }
}
