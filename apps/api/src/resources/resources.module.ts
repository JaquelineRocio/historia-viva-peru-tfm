import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { MlModule } from '../ml/ml.module';
import { ProjectEntity } from './entities/project.entity';
import { ResourceSegmentEntity } from './entities/resource-segment.entity';
import { ResourceEntity } from './entities/resource.entity';
import { PublicResourcesController, ResourcesController } from './resources.controller';
import { ResourcesService } from './resources.service';
import { FileStorageService } from './storage/file-storage.service';

@Module({
  imports: [TypeOrmModule.forFeature([ProjectEntity, ResourceEntity, ResourceSegmentEntity]), MlModule],
  controllers: [ResourcesController, PublicResourcesController],
  providers: [ResourcesService, FileStorageService],
})
export class ResourcesModule {}
