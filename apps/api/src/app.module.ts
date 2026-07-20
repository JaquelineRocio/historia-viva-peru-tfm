import { Module } from '@nestjs/common';
import { ConfigModule, ConfigService } from '@nestjs/config';
import { TypeOrmModule } from '@nestjs/typeorm';
import { AppController } from './app.controller';
import { AuthModule } from './auth/auth.module';
import { DatabaseBootstrapService } from './config/database-bootstrap.service';
import { buildTypeOrmOptions } from './config/typeorm.config';
import { DatasetsModule } from './datasets/datasets.module';
import { LabelsModule } from './labels/labels.module';
import { MlModule } from './ml/ml.module';
import { TrainingModule } from './training/training.module';
import { VideosModule } from './videos/videos.module';
import { ResourcesModule } from './resources/resources.module';

@Module({
  imports: [
    ConfigModule.forRoot({ isGlobal: true }),
    TypeOrmModule.forRootAsync({
      inject: [ConfigService],
      useFactory: (config: ConfigService) => buildTypeOrmOptions(config),
    }),
    AuthModule,
    MlModule,
    VideosModule,
    LabelsModule,
    DatasetsModule,
    TrainingModule,
    ResourcesModule,
  ],
  controllers: [AppController],
  providers: [DatabaseBootstrapService],
})
export class AppModule {}
